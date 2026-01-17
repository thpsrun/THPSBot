import re
from dataclasses import dataclass
from typing import Any


@dataclass
class THPSRunHelperResponse:
    embed_title: str
    players: str
    player_pfp: str
    time: str
    run_type: str
    delta: Any | None


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
        data: dict[str, dict],
    ) -> THPSRunHelperResponse | None:
        """Function that consolidates the retrevial of information from the thps.run API JSON."""
        if data["level"]:
            embed_title = f"{data['game']['name']} [IL]"
        else:
            embed_title = f"{data['game']['name']}"

        if data["place"] == 1:
            embed_title = "\U0001f3c6 (WR) " + embed_title
        elif data["place"] == 2:
            embed_title = "\U0001f948 (PB) " + embed_title
        elif data["place"] == 3:
            embed_title = "\U0001f949 (PB) " + embed_title
        elif data["status"]["obsolete"] is False:
            embed_title = "(PB) " + embed_title

        if isinstance(data["players"], list):
            players = ", ".join(player["name"] for player in data["players"])
            player_pfp = data["players"][0]["pfp"]
        else:
            players = data["players"]["name"]
            player_pfp = data["players"]["pfp"]

        time_key_map: dict[str, tuple[str, str]] = {
            "realtime": ("time_secs", "RTA"),
            "realtime_noloads": ("timenl_secs", "LRT"),
            "ingame": ("timeigt_secs", "IGT"),
        }

        default_time = data["times"]["defaulttime"]
        time_info = time_key_map.get(default_time)
        if time_info is None:
            return None
        time_key, run_type = time_info
        run_time = THPSRunHelper.format_time(data["times"][time_key])

        if data["record"]:
            if data["id"] != data["record"]["id"]:
                record_time = data["record"]["times"][time_key]
                pb_time = data["times"][time_key]

                record_time_str = THPSRunHelper.format_time(record_time)
                difference = THPSRunHelper.format_time(round(pb_time - record_time, 3))

                delta = f"{record_time_str} [+{difference}]"
            else:
                delta = None
        else:
            delta = "No Previous WR"

        return THPSRunHelperResponse(
            embed_title=embed_title,
            players=players,
            player_pfp=player_pfp,
            time=run_time,
            run_type=run_type,
            delta=delta,
        )
