import os
import random
import re
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
from thpsbot.helpers.task_helper import TaskHelper

if TYPE_CHECKING:
    from thpsbot.main import THPSBot

_FILENAME_RE = re.compile(r"^[A-Za-z0-9 _-]+$")


async def setup(bot: "THPSBot"):
    await bot.add_cog(ActivityCog(bot))


async def teardown(bot: "THPSBot"):
    await bot.remove_cog(name="GameActivities")  # type: ignore


class StatusConfirmView(discord.ui.View):
    def __init__(
        self,
        cog: "ActivityCog",
        status: str,
        force: bool,
    ) -> None:
        super().__init__(timeout=30)
        self.cog = cog
        self.status = status
        self.force = force
        self.message: discord.InteractionMessage | None = None

    async def on_timeout(
        self,
    ) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True

        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.success,
    )
    async def confirm(
        self,
        interaction: Interaction,
        button: discord.ui.Button,
    ) -> None:
        """Add the status, persist it, and optionally switch presence."""
        if self.status not in self.cog.gameslist:
            self.cog.gameslist.append(self.status)
            JsonHelper.save_json(self.cog.gameslist, "json/statuses.json")

        if self.force:
            await self.cog.bot.change_presence(activity=Game(name=self.status))

        self.stop()
        await interaction.response.edit_message(
            content=f"Status added: `{self.status}`",
            view=None,
        )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
    )
    async def cancel(
        self,
        interaction: Interaction,
        button: discord.ui.Button,
    ) -> None:
        """Cancel the add without touching the status list."""
        self.stop()
        await interaction.response.edit_message(
            content="Cancelled.",
            view=None,
        )


class PfpNameModal(discord.ui.Modal):
    filename: discord.ui.TextInput = discord.ui.TextInput(
        label="Filename",
        placeholder="Letters, digits, spaces, _ and - only",
        max_length=64,
        required=True,
    )

    def __init__(
        self,
        cog: "ActivityCog",
        image_url: str,
        file_extension: str,
    ) -> None:
        super().__init__(title="Name & save profile picture")
        self.cog = cog
        self.image_url = image_url
        self.file_extension = file_extension

    async def on_submit(
        self,
        interaction: Interaction,
    ) -> None:
        """Validate the name, download, resize, and save the pfp."""
        await interaction.response.defer(thinking=True, ephemeral=True)

        name = self.filename.value.strip()
        if not _FILENAME_RE.match(name):
            await interaction.followup.send(
                "Invalid filename. Use only letters, digits, spaces, `_` and `-`.",
                ephemeral=True,
            )
            return

        response = await AIOHTTPHelper.get_bytes(
            url=self.image_url,
            headers=None,
        )
        if not response.ok or not isinstance(response.data, bytes):
            await interaction.followup.send(
                "Image could not be downloaded.",
                ephemeral=True,
            )
            return

        try:
            image = Image.open(BytesIO(response.data))
            resized = image.resize((128, 128))
            resized.save(f"pfps/{name}{self.file_extension}")
        except Exception as e:
            self.cog.bot._log.error(e)
            await interaction.followup.send(
                "Image could not be saved.",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            f"{name} has been successfully added!",
            ephemeral=True,
        )


class PfpNameView(discord.ui.View):
    def __init__(
        self,
        cog: "ActivityCog",
        image_url: str,
        file_extension: str,
    ) -> None:
        super().__init__(timeout=120)
        self.cog = cog
        self.image_url = image_url
        self.file_extension = file_extension

    @discord.ui.button(
        label="Name & save",
        style=discord.ButtonStyle.primary,
    )
    async def name_and_save(
        self,
        interaction: Interaction,
        button: discord.ui.Button,
    ) -> None:
        """Open the filename modal in response to the button click."""
        self.stop()
        await interaction.response.send_modal(
            PfpNameModal(
                cog=self.cog,
                image_url=self.image_url,
                file_extension=self.file_extension,
            )
        )


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
    @TaskHelper.safe_task
    async def status_loop(self) -> None:
        game = Game(random.choice(self.gameslist))
        await self.bot.change_presence(activity=game, status=Status.online)

    @status_loop.before_loop
    async def before_status_loop(self) -> None:
        await self.bot.wait_until_ready()
        try:
            game = Game(random.choice(self.gameslist))
            await self.bot.change_presence(activity=game, status=Status.online)
        except discord.DiscordServerError:
            self.bot._log.warning("Discord 503 error in before_status_loop")

    @tasks.loop(hours=24)
    @TaskHelper.safe_task
    async def pfp_change(self) -> None:
        if ENV == "primary" and self.bot.user:
            pfp = random.choice(os.listdir("pfps/"))

            with open(f"pfps/{pfp}", "rb") as image:
                await self.bot.user.edit(avatar=image.read())

    @pfp_change.before_loop
    async def before_pfp_change(self) -> None:
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

            view = StatusConfirmView(
                cog=self,
                status=status,
                force=bool(force),
            )
            await interaction.response.send_message(
                f"Are you sure you want me to add the status:\n`{status}`?",
                view=view,
                ephemeral=True,
            )

            view.message = await interaction.original_response()
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
        if action.value == "add":
            if not image_url:
                await interaction.response.send_message(
                    "`image_url` is required for adding.",
                    ephemeral=True,
                )
                return

            url_parts = urlparse(image_url)
            file_extension = os.path.splitext(url_parts.path)[1].lower()

            if file_extension not in (".jpg", ".png"):
                await interaction.response.send_message(
                    "Only `.jpg` and `.png` images are supported.",
                    ephemeral=True,
                )
                return

            view = PfpNameView(
                cog=self,
                image_url=image_url,
                file_extension=file_extension,
            )
            await interaction.response.send_message(
                "Click below to name and save this profile picture.",
                view=view,
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            thinking=True,
            ephemeral=True,
        )

        if not pfp:
            pfp = random.choice(os.listdir("pfps/"))

        if not self.bot.user:
            await interaction.followup.send(
                "Bot user not available.",
                ephemeral=True,
            )
            return

        with open(f"pfps/{pfp}", "rb") as avatar_file:
            await self.bot.user.edit(avatar=avatar_file.read())

        await interaction.followup.send(
            f"Successfully changed to {pfp}!",
            ephemeral=True,
        )
