import os

from dotenv import load_dotenv

from thpsbot.helpers.json_helper import JsonHelper

load_dotenv()

ENV: str = "primary" if os.getenv("DEBUG") == "False" else "dev"

ROLES_LIST: dict[str, dict] = JsonHelper.load_json("json/roles.json")
CHANNELS_LIST: dict[str, dict] = JsonHelper.load_json("json/channels.json")
REACTIONS_LIST: dict[str, dict] = JsonHelper.load_json("json/reactions.json")
STATUSES_LIST: dict[str, dict] = JsonHelper.load_json("json/statuses.json")
LIVE_LIST: dict[str, dict] = JsonHelper.load_json("json/live.json")
TTVGAME_LIST: list = JsonHelper.load_json("json/ttvgames.json")
TTVGAME_IDS: list = JsonHelper.load_json("json/ttvgame_ids.json")
REMINDER_LIST: dict[str, dict] = JsonHelper.load_json("json/reminders.json")

GUILD_ID: int = int(CHANNELS_LIST[ENV]["server"])
ERROR_CHANNEL: int = int(CHANNELS_LIST[ENV]["error"])
SUBMISSION_CHANNEL: int = int(CHANNELS_LIST[ENV]["submission"])
PB_WR_CHANNEL: int = int(CHANNELS_LIST[ENV]["pb"])
STREAM_CHANNEL: int = int(CHANNELS_LIST[ENV]["stream"]["main"])
STREAM_OFF_THREAD: int = int(CHANNELS_LIST[ENV]["stream"]["thread"])

THPS_RUN_KEY: str = os.getenv("THPSRUN_API_KEY")
THPS_RUN_API: str = os.getenv("THPS_RUN_API")

SENTRY_SDN: str = os.getenv("SENTRY_SDN")

TTV_TOKEN: str = os.getenv("TWITCH_TOKEN")
TTV_ID: str = os.getenv("TWITCH_ID")

DEFAULT_IMG: str = os.getenv("DEFAULT_IMG")
BOT: str = os.getenv("BOT_NAME")

DISCORD_KEY: str = (
    os.getenv("DISCORD_PRIMARY_KEY")
    if os.getenv("DEBUG") == "False"
    else os.getenv("DISCORD_BETA_KEY")
)
