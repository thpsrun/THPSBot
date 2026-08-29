import logging
import os

from dotenv import load_dotenv

from thpsbot.helpers.json_helper import JsonHelper
from thpsbot.helpers.setup_json import setup_json

load_dotenv()

ENV: str = "primary" if os.getenv("DEBUG") == "False" else "dev"

setup_json()

AWARDS_LIST: dict[str, dict] = JsonHelper.load_json("json/awards.json")
CHANNELS_LIST: dict[str, dict] = JsonHelper.load_json("json/channels.json")
LIVE_LIST: dict[str, dict] = JsonHelper.load_json("json/live.json")
REACTIONS_LIST: dict[str, dict] = JsonHelper.load_json("json/reactions.json")
REMINDER_LIST: dict[str, dict] = JsonHelper.load_json("json/reminders.json")
ROLES_LIST: dict[str, dict] = JsonHelper.load_json("json/roles.json")
STATUSES_LIST: list[str] = JsonHelper.load_json("json/statuses.json")
SUBMISSIONS_LIST: dict[str, dict] = JsonHelper.load_json("json/submissions.json")
TTVGAME_IDS: list[str] = JsonHelper.load_json("json/ttvgame_ids.json")
TTVGAME_LIST: list[str] = JsonHelper.load_json("json/ttvgames.json")

GUILD_ID: int = int(CHANNELS_LIST[ENV]["server"])
ERROR_CHANNEL: int = int(CHANNELS_LIST[ENV]["error"])
SUBMISSION_CHANNEL: int = int(CHANNELS_LIST[ENV]["submission"])
PB_WR_CHANNEL: int = int(CHANNELS_LIST[ENV]["pb"])
STREAM_CHANNEL: int = int(CHANNELS_LIST[ENV]["stream"]["main"])
STREAM_OFF_THREAD: int = int(CHANNELS_LIST[ENV]["stream"]["thread"])

THPS_RUN_KEY: str = os.getenv("THPSRUN_API_KEY", "")
THPS_RUN_API: str = os.getenv("THPS_RUN_API", "")
THPS_RUN_SITE: str = os.getenv("THPS_RUN_SITE", "https://thps.run")

SENTRY_SDN: str = os.getenv("SENTRY_SDN", "")

TTV_TOKEN: str = os.getenv("TWITCH_TOKEN", "")
TTV_ID: str = os.getenv("TWITCH_ID", "")

DEFAULT_IMG: str = os.getenv("DEFAULT_IMG", "")
BOT: str = os.getenv("BOT_NAME", "THPSBot")

TTV_TIMEOUT: int = int(os.getenv("TTV_TIMEOUT", "5"))

DISCORD_KEY: str = (
    os.getenv("DISCORD_PRIMARY_KEY", "")
    if os.getenv("DEBUG") == "False"
    else os.getenv("DISCORD_BETA_KEY", "")
)


def validate_config() -> None:
    """Fail fast at boot if the active ENV is missing required config values."""
    # Token comes from .env; the rest come from the active half of channels.json.
    token_var = "DISCORD_PRIMARY_KEY" if ENV == "primary" else "DISCORD_BETA_KEY"
    problems: list[str] = []

    if not DISCORD_KEY:
        problems.append(f"  - .env: {token_var} is empty")

    channel_checks: list[tuple[int, str]] = [
        (GUILD_ID, f'channels.json["{ENV}"]["server"]'),
        (ERROR_CHANNEL, f'channels.json["{ENV}"]["error"]'),
        (SUBMISSION_CHANNEL, f'channels.json["{ENV}"]["submission"]'),
        (PB_WR_CHANNEL, f'channels.json["{ENV}"]["pb"]'),
        (STREAM_CHANNEL, f'channels.json["{ENV}"]["stream"]["main"]'),
        (STREAM_OFF_THREAD, f'channels.json["{ENV}"]["stream"]["thread"]'),
    ]
    for value, key in channel_checks:
        if value == 0:
            problems.append(f"  - runtime json/channels.json: {key} is unset (0)")

    if problems:
        log = logging.getLogger("THPSBot")
        message = (
            f"Configuration is incomplete for ENV={ENV!r}. Fix the following, then "
            "restart:\n"
            + "\n".join(problems)
            + "\n\nEdit the runtime json/channels.json (NOT the .json/ templates) and "
            "fill in the real Discord server/channel IDs, and set the Discord token in "
            ".env."
        )
        log.critical(message)
        print(message)
        raise SystemExit(1)
