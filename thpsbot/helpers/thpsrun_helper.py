import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from thpsbot.helpers.aiohttp_helper import AIOHTTPHelper
from thpsbot.helpers.config_helper import THPS_RUN_API, THPS_RUN_SITE
from thpsbot.helpers.duration_helper import format_gap, format_reign
from thpsbot.models import (
    PlayerRunInline,
    THPSRunCategory,
    THPSRunGame,
    THPSRunHistory,
    THPSRunLevel,
    THPSRunRuns,
)

if TYPE_CHECKING:
    from thpsbot.main import THPSBot

_log = logging.getLogger(__name__)

# v4 timing-method labels (resolved_primary_method / import-issue methods).
METHOD_LABELS: dict[str, str] = {"rta": "RTA", "lrt": "LRT", "igt": "IGT"}
TIMING_NAMES: dict[str, str] = {
    "rta": "Real Time",
    "lrt": "Load-Removed Time",
    "igt": "In-Game Time",
}


@dataclass
class THPSRunHelperResponse:
    embed_title: str
    players: str
    time: str
    run_type: str
    delta: Any | None
    warnings: list | None


class THPSRunHelper:
    @staticmethod
    def get_run_id(
        url: str,
    ) -> str | None:
        pattern = r"^(https?:\/\/)?(www\.)?speedrun\.com\/[^\/]+\/runs?\/([a-zA-Z0-9]+)"
        match = re.match(pattern, url)
        return match.group(3) if match else None

    @staticmethod
    def format_time(
        seconds: float,
    ) -> str:
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds_int = divmod(remainder, 60)
        milliseconds = int(round((seconds - int(seconds)) * 1000))

        return f"{hours}:{minutes:02}:{seconds_int:02}" + (
            f".{milliseconds:03}" if milliseconds > 0 else ""
        )

    @staticmethod
    def get_run_data(
        data: THPSRunRuns,
    ) -> THPSRunHelperResponse | None:
        embed_title = (
            data.game.name if isinstance(data.game, THPSRunGame) else (data.game or "")
        )

        if data.level:
            embed_title = embed_title + " [IL]"

        if data.obsolete:
            embed_title = "(PB) " + embed_title
        elif data.place == 1:
            embed_title = "\U0001f3c6 (WR) " + embed_title + " \U0001f3c6"
        elif data.place == 2:
            embed_title = "\U0001f948 (PB) " + embed_title + " \U0001f948"
        elif data.place == 3:
            embed_title = "\U0001f949 (PB) " + embed_title + " \U0001f949"

        players = ", ".join(player.name for player in data.players)

        method = data.resolved_primary_method or ""
        run_type = METHOD_LABELS.get(method, method.upper())

        if data.times.p_time:
            run_time = data.times.p_time
        elif data.times.p_time_secs is not None:
            run_time = THPSRunHelper.format_time(data.times.p_time_secs)
        else:
            run_time = "Unknown"

        return THPSRunHelperResponse(
            embed_title=embed_title,
            players=players,
            time=run_time,
            run_type=run_type,
            delta=None,
            warnings=None,
        )

    @staticmethod
    async def get_import_issues(
        bot: "THPSBot",
        run_id: str,
    ) -> list[str]:
        """Fetch v4 import-validation flags for a run and format them as embed lines."""
        try:
            resp = await AIOHTTPHelper.get(
                url=f"{THPS_RUN_API}/runs/{run_id}/import-issues",
                headers=bot.thpsrun_header,
            )
        except Exception as e:
            _log.warning("import-issues fetch failed for %s", run_id, exc_info=e)
            return []

        if not resp.ok or not isinstance(resp.data, dict):
            if resp.status in (401, 403):
                _log.error(
                    "import-issues %s: %s (check X-API-Key games.audit.view scope)",
                    resp.status,
                    run_id,
                )
            return []

        lines: list[str] = []
        for issue in resp.data.get("import_issues") or []:
            itype = issue.get("type")
            if itype == "missing_timing_methods":
                names = [TIMING_NAMES.get(m, m) for m in issue.get("methods", [])]
                lines.append("Missing Timing: " + ", ".join(names))
            elif itype == "invalid_video_host":
                lines.append("Non-YouTube Video: " + str(issue.get("url", "")))
            else:
                lines.append("Unknown Issue: " + str(itype))
        return lines

    @staticmethod
    async def get_record_delta(
        bot: "THPSBot",
        run: THPSRunRuns,
    ) -> dict | None:
        """Compute a run's delta to the WR on its exact leaderboard (two public GETs)."""
        r_secs = run.times.p_time_secs
        if r_secs is None:
            return None

        game_id = run.game.id if isinstance(run.game, THPSRunGame) else run.game
        category_id = (
            run.category.id
            if isinstance(run.category, THPSRunCategory)
            else run.category
        )
        level_id = run.level.id if isinstance(run.level, THPSRunLevel) else run.level

        query = (
            f"{THPS_RUN_API}/runs/all?game_id={game_id}"
            f"&category_id={category_id}&place=1&status=verified"
        )
        if level_id:
            query += f"&level_id={level_id}"

        resp = await AIOHTTPHelper.get(url=query, headers=bot.thpsrun_header)
        if not resp.ok or not isinstance(resp.data, list):
            return {"record": None}

        wr: THPSRunRuns | None = None
        for raw in resp.data:
            candidate = THPSRunRuns(**raw)
            cand_level = (
                candidate.level.id
                if isinstance(candidate.level, THPSRunLevel)
                else candidate.level
            )
            if cand_level == level_id and candidate.variables == run.variables:
                wr = candidate
                break

        if wr is None:
            return {"record": None}

        w_secs = wr.times.p_time_secs
        if w_secs is None:
            return None

        delta = round(r_secs - w_secs, 3)
        return {
            "run_id": run.id,
            "run_secs": r_secs,
            "run_time": run.times.p_time,
            "wr_id": wr.id,
            "wr_secs": w_secs,
            "wr_time": wr.times.p_time,
            "delta_secs": delta,
            "is_record": delta <= 0,
        }

    @staticmethod
    async def _resolve_value_slugs(
        bot: "THPSBot",
        run: THPSRunRuns,
    ) -> list[str] | None:
        """Resolve a run's variable value-IDs to value slugs for the `values=` param."""
        slugs: list[str] = []
        for value_id in (run.variables or {}).values():
            resp = await AIOHTTPHelper.get(
                url=f"{THPS_RUN_API}/variables/values/{value_id}",
                headers=bot.thpsrun_header,
            )
            if not resp.ok or not isinstance(resp.data, dict):
                return None
            slug = resp.data.get("slug")
            if not slug:
                return None
            slugs.append(slug)
        return slugs

    @staticmethod
    async def build_leaderboard_url(
        bot: "THPSBot",
        run: THPSRunRuns,
    ) -> str | None:
        """Build the thps.run frontend leaderboard URL for a run, or None.

        Resolves the run's game/category/level slugs and variable value-slugs into the public
        leaderboard URL (the same board the run lives on). Value-slugs are emitted in the order the
        API returns them.

        Arguments:
            bot (THPSBot): The running bot instance (for the API auth header).
            run (THPSRunRuns): A run with embedded game/category/level objects.

        Returns:
            url (str | None): The frontend leaderboard URL, or None if unbuildable.
        """
        game = run.game if isinstance(run.game, THPSRunGame) else None
        category = run.category if isinstance(run.category, THPSRunCategory) else None
        if not (game and game.slug and category and category.slug):
            return None
        level = run.level if isinstance(run.level, THPSRunLevel) else None

        slugs = await THPSRunHelper._resolve_value_slugs(bot, run)
        if slugs is None:
            return None

        if level and level.slug:
            path = f"{game.slug}/ils/{level.slug}/{category.slug}"
        else:
            path = f"{game.slug}/{category.slug}"
        if slugs:
            path += "/" + "/".join(slugs)

        return f"{THPS_RUN_SITE}/{path}"

    @staticmethod
    def build_leaderboard_url_inline(
        run: PlayerRunInline,
    ) -> str | None:
        """Build the thps.run leaderboard URL from an inline player-run object.

        Uses the slugs and ordered value_slugs already present in the player-runs payload, so it
        performs no API calls. Returns None when a required slug is missing.

        Arguments:
            run (PlayerRunInline): A recent-run entry from a player payload.

        Returns:
            url (str | None): The frontend leaderboard URL, or None if unbuildable.
        """
        game_slug = run.game.slug if run.game else None
        category_slug = run.category.slug if run.category else None
        if not (game_slug and category_slug):
            return None
        level_slug = run.level.slug if run.level else None

        if level_slug:
            path = f"{game_slug}/ils/{level_slug}/{category_slug}"
        else:
            path = f"{game_slug}/{category_slug}"
        if run.value_slugs:
            path += "/" + "/".join(run.value_slugs)

        return f"{THPS_RUN_SITE}/{path}"

    @staticmethod
    async def get_wr_reign(
        bot: "THPSBot",
        run: THPSRunRuns,
    ) -> str | None:
        """Subtext line naming the previous WR holder and how long it lasted, or None."""
        game = run.game if isinstance(run.game, THPSRunGame) else None
        category = run.category if isinstance(run.category, THPSRunCategory) else None
        if not (game and game.slug and category and category.slug):
            return None
        level = run.level if isinstance(run.level, THPSRunLevel) else None

        try:
            slugs = await THPSRunHelper._resolve_value_slugs(bot, run)
            if slugs is None:
                return None

            if level and level.slug:
                url = (
                    f"{THPS_RUN_API}/history/{game.slug}"
                    f"/level/{level.slug}/{category.slug}"
                )
            else:
                url = f"{THPS_RUN_API}/history/{game.slug}/category/{category.slug}"
            if slugs:
                url += "?values=" + ",".join(slugs)

            resp = await AIOHTTPHelper.get(url=url, headers=bot.thpsrun_header)
            if not resp.ok or not isinstance(resp.data, dict):
                return None

            history = THPSRunHistory(**resp.data)

            current = next((e for e in history.entries if e.run_id == run.id), None)
            if current is None or current.end_date is not None:
                return None

            candidates = [
                e
                for e in history.entries
                if e.run_id != run.id and e.end_date and e.start_date
            ]
            if not candidates:
                return None

            prev = max(
                candidates,
                key=lambda e: (
                    datetime.fromisoformat(e.end_date),
                    -(e.history_time_secs or 0.0),
                    -datetime.fromisoformat(e.start_date).timestamp(),
                ),
            )
            start = datetime.fromisoformat(prev.start_date)
            end = datetime.fromisoformat(prev.end_date)
            if end <= start:
                return None

            name = prev.players[0].name if prev.players else None
            if not name:
                return None
            holder = f"[{name}]({THPS_RUN_SITE}/player/{name})"

            if prev.history_time:
                link = prev.arch_video or prev.video
                time_part = (
                    f" ([{prev.history_time}]({link}))"
                    if link
                    else f" ({prev.history_time})"
                )
            else:
                time_part = ""

            gap = ""
            r_secs = run.times.p_time_secs
            if r_secs is not None and prev.history_time_secs is not None:
                diff = r_secs - prev.history_time_secs
                if diff < 0:
                    formatted = format_gap(diff)
                    if formatted:
                        gap = f" [-{formatted}]"

            return (
                f"\n-# Last WR Holder: {holder}{time_part}{gap}"
                f"\n-# The last record lasted {format_reign(start, end)}."
            )
        except Exception as e:
            _log.warning("get_wr_reign failed for %s", run.id, exc_info=e)
            return None
