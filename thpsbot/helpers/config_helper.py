import os

from dotenv import load_dotenv

from thpsbot.helpers.json_helper import JsonHelper

load_dotenv()

ENV: str = "primary" if os.getenv("DEBUG") == "False" else "dev"

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
