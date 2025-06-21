import logging
import os
import time
from typing import TypeVar

import discord
import sentry_sdk
from discord import Intents
from discord.ext import commands

from thpsbot.helpers.config_helper import (
    DISCORD_KEY,
    ENV,
    ERROR_CHANNEL,
    GUILD_ID,
    ROLES_LIST,
    SENTRY_SDN,
    THPS_RUN_KEY,
)
from thpsbot.helpers.embed_helper import EmbedCreator
from thpsbot.helpers.setup_json import setup_json
from thpsbot.helpers.setup_logging import setup_logging

T = TypeVar("T")


class BotContext(EmbedCreator, commands.Context):
    bot: "THPSBot"


class THPSBot(commands.Bot):
    def __init__(self, **kwargs):
        setup_logging()
        setup_json()

        intent = Intents.default()
        intent.message_content = True
        intent.reactions = True
        intent.members = True
        intent.guilds = True

        self._log = logging.getLogger("THPSBot")
        self.case_insensitive = True
        self.start_time = time.time()

        self.thpsrun_header: dict[str, str] = {
            "Authorization": f"Api-Key {THPS_RUN_KEY}"
        }
        self.roles: dict[dict, str] = ROLES_LIST[ENV]
        self._log.info("Bot successfully started...")

        if ENV == "primary":
            sentry_sdk.init(
                dsn=SENTRY_SDN,
                send_default_pii=True,
                traces_sample_rate=1.0,
            )
        else:
            self._log.info("Currently in dev mode; skipping Sentry...")

        super().__init__(
            command_prefix="/", intents=intent, case_insensitive=True, **kwargs
        )

    async def setup_hook(self) -> None:
        """Loads modules after loading the bot."""
        self._log.info("setup_hook initialized...")

        self.base = BaseCommands(self)
        self.errorchannel = await self.fetch_channel(ERROR_CHANNEL)

        self.tree.clear_commands(guild=discord.Object(id=GUILD_ID))
        self.tree.clear_commands(guild=None)
        await self.tree.sync(guild=discord.Object(id=GUILD_ID))
        await self.tree.sync(guild=None)

        await self.add_cog(self.base)

        modules_dir = os.path.join(os.path.dirname(__file__), "modules")
        for file in os.listdir(modules_dir):
            if file.endswith(".py") and not file.startswith("__"):
                module_name = file[:-3]
                try:
                    await self.load_extension(f"thpsbot.modules.{module_name}")
                    self._log.info(f"Loaded module {module_name}")
                except commands.ExtensionError as e:
                    self._log.error(f"Failed to load module {module_name}", exc_info=e)

        await self.tree.sync(guild=discord.Object(id=GUILD_ID))


class BaseCommands(commands.Cog):
    def __init__(self, bot: THPSBot) -> None:
        self.bot = bot


def main():
    bot = THPSBot()
    bot.run(DISCORD_KEY)


if __name__ == "__main__":
    main()
