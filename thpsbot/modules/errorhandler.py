import sys
from typing import TYPE_CHECKING

import discord
import sentry_sdk
from discord import Interaction, app_commands
from discord.ext.commands import Cog, ExtensionError

if TYPE_CHECKING:
    from thpsbot.main import THPSBot


async def setup(bot: "THPSBot"):
    cog = ErrorHandler(bot)
    await bot.add_cog(cog)

    bot.tree.on_error = cog.on_app_command_error


async def teardown(bot: "THPSBot"):
    await bot.remove_cog(name="ErrorHandler")  # type: ignore


class ErrorHandler(
    Cog,
    name="ErrorHandler",
    description="Manages THPSBot's errors",
):
    def __init__(self, bot: "THPSBot") -> None:
        self.bot = bot

    @Cog.listener()
    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        _, error, _ = sys.exc_info()

        if error is None:
            self.bot._log.warning(
                f"on_error called for {event_method} with no exception"
            )
            return

        if isinstance(error, (discord.DiscordServerError, TimeoutError)):
            self.bot._log.warning(f"EVENT:{event_method} - {type(error).__name__}")
            return

        self.bot._log.error(f"EVENT:{event_method}", exc_info=error)
        sentry_sdk.capture_exception(error)

    async def on_app_command_error(
        self, interaction: Interaction, error: app_commands.AppCommandError
    ) -> None:
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                "You do not have the permissions to run this command.",
                ephemeral=True,
            )
        elif isinstance(error, app_commands.errors.CommandInvokeError):
            await interaction.response.send_message(
                "An error occurred when looking up that object. Does it exist?",
                ephemeral=True,
            )

            self.bot._log.error("COMMAND_ERROR", exc_info=error)
        elif isinstance(error, app_commands.errors.CommandNotFound):
            self.bot._log.error("CMD_NOT_FOUND", exc_info=error)
        elif isinstance(error, discord.Forbidden) or isinstance(
            error, app_commands.errors.BotMissingPermissions
        ):
            await interaction.response.send_message(
                "An error occurred. Does the bot have the right permissions to do this?",
                ephemeral=True,
            )

            self.bot._log.error("FORBIDDEN", exc_info=error)
        elif isinstance(error, discord.NotFound):
            await interaction.response.send_message(
                "An error occurred. That content was not found.",
                ephemeral=True,
            )

            self.bot._log.error("NOTFOUND", exc_info=error)
        elif isinstance(error, discord.HTTPException):
            await interaction.response.send_message(
                "An error occurred with Discord's API. Try again?",
                ephemeral=True,
            )

            self.bot._log.exception("HTTP_EXCEPTION", exc_info=error)
        elif isinstance(error, discord.ClientException):
            await interaction.response.send_message(
                "An unknown error occurred", ephemeral=True
            )

            self.bot._log.exception("CLIENT_EXCEPTION", exc_info=error)
            sentry_sdk.capture_exception(error)
        elif isinstance(error, ExtensionError):
            self.bot._log.error("EXTENSION_ERROR", exc_info=error)
            sentry_sdk.capture_exception(error)
        elif isinstance(error, ValueError):
            self.bot._log.error("VALUE_ERROR", exc_info=error)
            sentry_sdk.capture_exception(error)
        elif isinstance(error, AttributeError):
            self.bot._log.error("ATTR_ERROR", exc_info=error)
            sentry_sdk.capture_exception(error)
        elif isinstance(error, discord.DiscordServerError):
            self.bot._log.error("SERVER_ERROR", exc_info=error)
        else:
            if interaction.response.is_done():
                await interaction.followup.send(
                    "An unexpected error occurred. Check logs.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "An unexpected error occurred. Check logs.",
                    ephemeral=True,
                )

            self.bot._log.error("UNKNOWN", exc_info=error)
