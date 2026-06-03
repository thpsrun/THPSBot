import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from thpsbot.helpers.aiohttp_helper import AIOHTTPHelper
from thpsbot.helpers.config_helper import THPS_RUN_API
from thpsbot.models import (
    THPSRunCategory,
    THPSRunGame,
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
