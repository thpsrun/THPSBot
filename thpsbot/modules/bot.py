import os
import random
from io import BytesIO
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import discord
from discord import Game, Interaction, Status, app_commands
from discord.ext import commands, tasks
from discord.ext.commands import Cog
from PIL import Image

from thpsbot.helpers.aiohttp_helper import AIOHTTPHelper
from thpsbot.helpers.autocomplete_helper import get_pfp_filenames
from thpsbot.helpers.config_helper import ENV, GUILD_ID, STATUSES_LIST
from thpsbot.helpers.json_helper import JsonHelper

if TYPE_CHECKING:
    from thpsbot.main import THPSBot


async def setup(bot: "THPSBot"):
    await bot.add_cog(ActivityCog(bot))


async def teardown(bot: "THPSBot"):
    await bot.remove_cog(name="GameActivities")


class ActivityCog(
    Cog,
    name="GameActivities",
    description="Manages THPSBot's statuses",
):
    def __init__(self, bot: "THPSBot") -> None:
        self.bot = bot
        self.gameslist: list = STATUSES_LIST

    async def cog_load(self) -> None:
        self.bot.tree.add_command(
            self.main_cmd_group,
            guild=discord.Object(id=GUILD_ID),
            override=True,
        )
        self.status_loop.start()
        self.pfp_change.start()

    async def cog_unload(self) -> None:
        self.status_loop.cancel()
        self.pfp_change.cancel()

    @tasks.loop(minutes=60)
    async def status_loop(self) -> None:
        """Changes the bot's status every 60 minutes."""
        try:
            game = Game(random.choice(self.gameslist))
            await self.bot.change_presence(activity=game, status=Status.online)
        except discord.DiscordServerError:
            self.bot._log.warning("Discord 503 error in status_loop, will retry next loop")

    @status_loop.before_loop
    async def before_status_loop(self) -> None:
        """Changes the bot's status upon initialization."""
        await self.bot.wait_until_ready()
        try:
            game = Game(random.choice(self.gameslist))
            await self.bot.change_presence(activity=game, status=Status.online)
        except discord.DiscordServerError:
            self.bot._log.warning("Discord 503 error in before_status_loop")

    @tasks.loop(hours=24)
    async def pfp_change(self) -> None:
        """Changes the bot's profile picture every 24 hours."""
        if ENV == "primary" and self.bot.user:
            try:
                pfp = random.choice(os.listdir("pfps/"))

                with open(f"pfps/{pfp}", "rb") as image:
                    await self.bot.user.edit(avatar=image.read())
            except discord.DiscordServerError:
                self.bot._log.warning(
                    "Discord 503 error in pfp_change, will retry next loop"
                )

    @pfp_change.before_loop
    async def before_pfp_change(self) -> None:
        """Changes the bot's profile picture upon initialization."""
        if ENV == "primary":
            await self.bot.wait_until_ready()
            if not self.bot.user:
                return
            try:
                pfp = random.choice(os.listdir("pfps/"))

                with open(f"pfps/{pfp}", "rb") as image:
                    await self.bot.user.edit(avatar=image.read())
            except discord.DiscordServerError:
                self.bot._log.warning("Discord 503 error in before_pfp_change")

    ###########################################################################
    # main_cmd_group Commands
    ###########################################################################
    main_cmd_group = app_commands.Group(
        name="bot",
        description="Commands related to THPSBot's functionality.",
    )

    @main_cmd_group.command(
        name="ping",
        description="See if the bot is offline and responding properly!",
    )
    async def ping(self, interaction: Interaction) -> None:
        """See if the bot is offline and responding properly!"""
        await interaction.response.send_message(
            f"Hello, {interaction.user.mention}! If you are seeing this, I am online! "
            f"If something is broken, blame Packle.",
            ephemeral=True,
        )

    @main_cmd_group.command(
        name="reload",
        description="Reload all modules loaded into THPSBot!",
    )
    async def reload(self, interaction: Interaction) -> None:
        """Reload all modules loaded into THPSBot!"""
        await interaction.response.defer(thinking=True, ephemeral=True)

        extension_names = list(self.bot.extensions.keys())
        failed = []
        for extension in extension_names:
            try:
                await self.bot.reload_extension(extension, package="modules")
                self.bot._log.info(f"Reloaded {extension}...")
            except commands.ExtensionError:
                self.bot._log.error(f"Failed to load {extension}; ignoring")
                failed.append(extension)
        if not failed:
            await interaction.followup.send(
                "Modules reloaded!",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                f"{', '.join(failed)} failed to reload. See log for errors.",
                ephemeral=True,
            )

    ###########################################################################

    @main_cmd_group.command(
        name="status",
        description="Adds, removes, or force changes statuses for THPSBot.",
    )
    @app_commands.describe(
        action="Add, remove, or force change statuses.",
        status='What is the name of the "game" you want THPSBot to potentially play?',
        force='If True, this will force the bot to change to the "game" when added successfully.',
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="add", value="add"),
            app_commands.Choice(name="remove", value="remove"),
            app_commands.Choice(name="force", value="force"),
        ]
    )
    async def status(
        self,
        interaction: Interaction,
        action: app_commands.Choice[str],
        status: str | None,
        force: bool | None,
    ) -> None:
        """Adds, removes, or force changes statuses for THPSBot."""
        if action.value == "add":
            if not status:
                await interaction.response.send_message(
                    "The `status` parameter is required for adding.",
                    ephemeral=True,
                )
                return
            status = status.replace('"', "")

            if len(status) > 75:
                await interaction.response.send_message(
                    f"{status} is {len(status)} characters long! Max is 75 characters.",
                    ephemeral=True,
                )
                return

            await interaction.response.send_message(
                f"Are you sure you want me to set the status to:\n`{status}`\n"
                "Reply with `yes` to confirm.",
                ephemeral=True,
            )

            def check(m: discord.Message) -> bool:
                return m.author == interaction.user and m.channel == interaction.channel

            try:
                msg = await self.bot.wait_for(
                    "message",
                    check=check,
                    timeout=10,
                )
                if msg.content.lower() != "yes":
                    await interaction.followup.send(
                        "Cancelled.",
                        ephemeral=True,
                    )

                await msg.delete()
            except Exception:
                await interaction.followup.send(
                    "No confirmation received. Cancelled.",
                    ephemeral=True,
                )
                return

            if force:
                await self.bot.change_presence(activity=Game(name=status))

                await interaction.followup.send(
                    f"Status updated to: `{status}`",
                    ephemeral=True,
                )

            if status not in self.gameslist:
                self.gameslist.append(status)
                JsonHelper.save_json(self.gameslist, "json/statuses.json")
        elif action.value == "remove":
            if status in self.gameslist:
                self.gameslist.remove(status)
                JsonHelper.save_json(self.gameslist, "json/statuses.json")

                await interaction.response.send_message(
                    f"{status} has been removed successfully.",
                    ephemeral=True,
                )
                return

            await interaction.response.send_message(
                f"{status} is not in the statuses table.",
                ephemeral=True,
            )
        else:
            game = Game(random.choice(self.gameslist))

            await self.bot.change_presence(activity=game)
            await interaction.response.send_message(
                f"New random status set: `{game.name}`",
                ephemeral=True,
            )

    ###########################################################################

    @main_cmd_group.command(
        name="pfp",
        description="Adds or force change profile pictures for THPSBot.",
    )
    @app_commands.describe(
        action="Add or force profile pictures.",
        image_url="Required for add. Full URL to the picture you want to add to THPSBot.",
        pfp="Optional. Choose the profile picture you want! If none is set for force, it's random",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="add", value="add"),
            app_commands.Choice(name="force", value="force"),
        ]
    )
    @app_commands.autocomplete(pfp=get_pfp_filenames)
    async def pfp(
        self,
        interaction: Interaction,
        action: app_commands.Choice[str],
        image_url: str | None,
        pfp: str | None,
    ) -> None:
        """Adds or force change profile pictures for THPSBot."""
        await interaction.response.defer(
            thinking=True,
            ephemeral=True,
        )

        if action.value == "add":
            if not image_url:
                await interaction.followup.send(
                    "`image_url` is required for adding.",
                    ephemeral=True,
                )
                return

            url_parts = urlparse(image_url)
            file_extension = os.path.splitext(url_parts.path)[1]

            if file_extension.lower() in (".jpg", ".png"):
                response = await AIOHTTPHelper.get(
                    url=image_url,
                    headers=None,
                )

                if not response.ok:
                    await interaction.followup.send(
                        "Image could not be downloaded.",
                        ephemeral=True,
                    )
                    return

                image = Image.open(BytesIO(response.data))
                image = image.resize((128, 128))

                await interaction.followup.send(
                    "What do you want the name of the filename to be?",
                    ephemeral=True,
                )

                def check(m: discord.Message) -> bool:
                    return (
                        m.author == interaction.user
                        and m.channel == interaction.channel
                    )

                try:
                    msg = await self.bot.wait_for(
                        "message",
                        check=check,
                        timeout=10,
                    )
                    new_filename = msg.content
                    await msg.delete()

                    image.save(f"pfps/{new_filename}{file_extension}")

                    await interaction.followup.send(
                        f"{new_filename} has been successfully added!",
                        ephemeral=True,
                    )
                except Exception as e:
                    await interaction.followup.send(
                        "No confirmation received. Cancelled.",
                        ephemeral=True,
                    )
                    self.bot._log.error(e)
                    return
        else:
            if not pfp:
                pfp = random.choice(os.listdir("pfps/"))

            if not self.bot.user:
                await interaction.followup.send(
                    "Bot user not available.",
                    ephemeral=True,
                )
                return

            with open(f"pfps/{pfp}", "rb") as image:
                await self.bot.user.edit(avatar=image.read())

            await interaction.followup.send(
                f"Successfully changed to {pfp}!",
                ephemeral=True,
            )
