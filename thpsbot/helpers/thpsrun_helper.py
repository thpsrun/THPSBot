import re
from dataclasses import dataclass
from typing import Any

from thpsbot.models.thpsrun_api import THPSRunRuns


@dataclass
class THPSRunHelperResponse:
    embed_title: str
    players: str
    player_pfp: str | None
    time: str
    run_type: str
    delta: Any | None
    warnings: list | None


class THPSRunHelper:
    @staticmethod
    def get_run_id(
        url: str,
    ) -> str | None:
        """Ensures that either `www.speedrun.com` or `speedrun.com` is used and grabs the run ID."""
        pattern = r"^(https?:\/\/)?(www\.)?speedrun\.com\/[^\/]+\/runs?\/([a-zA-Z0-9]+)"
        match = re.match(pattern, url)
        return match.group(3) if match else None

    @staticmethod
    def format_time(
        seconds: int,
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
        """Function that consolidates the retrevial of information from the thps.run API JSON."""
        embed_title = f"{data.game.name}"
        warnings = []

        if data.level:
            embed_title = embed_title + " [IL]"

        if data.place == 1:
            embed_title = "\U0001f3c6 (WR) " + embed_title + " \U0001f3c6"
        elif data.place == 2:
            embed_title = "\U0001f948 (PB) " + embed_title + " \U0001f948"
        elif data.place == 3:
            embed_title = "\U0001f949 (PB) " + embed_title + " \U0001f949"
        elif data.place is False:
            embed_title = "(PB) " + embed_title

        if isinstance(data.players, list):
            players = ", ".join(player.name for player in data.players)
            player_pfp = data.players[0].pfp
        else:
            players = data.players.name
            player_pfp = data.players.pfp

        time_key_map: dict[str, tuple[str, str]] = {
            "realtime": ("time_secs", "RTA"),
            "realtime_noloads": ("timenl_secs", "LRT"),
            "ingame": ("timeigt_secs", "IGT"),
        }

        default_time = data.times.defaulttime
        time_info = time_key_map.get(default_time)
        if time_info is None:
            return None

        time_key, run_type = time_info
        run_time = THPSRunHelper.format_time(getattr(data.times, time_key))

        if data.record:
            if data.id is not data.record.id:
                record_time = getattr(data.record.times, time_key)
                pb_time = getattr(data.times, time_key)

                record_time_str = THPSRunHelper.format_time(record_time)
                difference = THPSRunHelper.format_time(round(pb_time - record_time, 3))

                delta = f"{record_time_str} [+{difference}]"
            else:
                delta = None
        else:
            delta = "No Previous WR"

        # Checks to see if the run has a video AND if it is from YouTube.
        # If neither occurs, a warning is added.
        youtube = ["youtube.com", "youtu.be"]
        if not data.videos.video:
            warnings.append("No Video Detected")
        elif not any(y in data.videos.video for y in youtube):
            warnings.append("Non-YouTube Video Detected")

        # Checks if the game expects a timing method but the run is missing that time.
        expected_time_method = (
            data.game.idefaulttime if data.level else data.game.defaulttime
        )
        expected_time_info = time_key_map.get(expected_time_method)
        if expected_time_info:
            expected_time_key, expected_label = expected_time_info
            if getattr(data.times, expected_time_key) is None:
                warnings.append(f"Missing Expected Time ({expected_label})")

        # For ILs, checks if extra time fields are populated beyond the expected idefaulttime.
        if data.level:
            il_time_info = time_key_map.get(data.game.idefaulttime)
            if il_time_info:
                il_time_key, _ = il_time_info
                extra_times = []
                for _, (key, label) in time_key_map.items():
                    if key != il_time_key and getattr(data.times, key) is not None:
                        extra_times.append(label)
                if extra_times:
                    warnings.append(f"IL Has Extra Timings: {', '.join(extra_times)}")

        return THPSRunHelperResponse(
            embed_title=embed_title,
            players=players,
            player_pfp=player_pfp,
            time=run_time,
            run_type=run_type,
            delta=delta,
            warnings=warnings,
        )
