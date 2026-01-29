import io
import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import discord
from discord import Interaction, app_commands
from discord.ext.commands import Cog

from thpsbot.helpers.auth_helper import is_admin
from thpsbot.helpers.config_helper import AWARDS_LIST, ENV, GUILD_ID
from thpsbot.helpers.json_helper import JsonHelper

if TYPE_CHECKING:
    from thpsbot.main import THPSBot


async def setup(bot: "THPSBot"):
    await bot.add_cog(AwardsCog(bot))


async def teardown(bot: "THPSBot"):
    await bot.remove_cog(name="Awards")  # type: ignore


class AwardsCog(
    Cog, name="Awards", description="Mark messages for end-of-year awards."
):
    def __init__(self, bot: "THPSBot") -> None:
        self.bot = bot
        self.awards_data: dict = AWARDS_LIST[ENV]

    async def cog_load(self) -> None:
        self.bot.tree.add_command(
            self.awards_group,
            guild=discord.Object(id=GUILD_ID),
            override=True,
        )

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(
            self.awards_group.name,
            type=discord.AppCommandType.chat_input,
        )

    ###########################################################################
    # awards_group Commands
    ###########################################################################
    awards_group = app_commands.Group(
        name="awards", description="Commands for marking messages for awards."
    )

    @awards_group.command(
        name="setreaction",
        description="Set the emoji reaction that marks messages for awards.",
    )
    @app_commands.describe(emoji="The emoji to use for marking messages.")
    @is_admin()
    async def setreaction(self, interaction: Interaction, emoji: str) -> None:
        self.awards_data["reaction"] = emoji
        AWARDS_LIST[ENV] = self.awards_data
        JsonHelper.save_json(AWARDS_LIST, "json/awards.json")

        await interaction.response.send_message(
            f"Awards reaction set to {emoji}. "
            "Any message reacted with this emoji will be marked for awards.",
            ephemeral=True,
        )

    @awards_group.command(
        name="export",
        description="Export all marked messages as a JSON file.",
    )
    @is_admin()
    async def export(self, interaction: Interaction) -> None:
        marked = self.awards_data.get("marked_messages", {})

        if not marked:
            await interaction.response.send_message(
                "No messages have been marked for awards yet.",
                ephemeral=True,
            )
            return

        export_data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_messages": len(marked),
            "messages": list(marked.values()),
        }

        json_str = json.dumps(export_data, indent=4, ensure_ascii=False)
        file = discord.File(
            io.BytesIO(json_str.encode("utf-8")),
            filename=f"awards_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json",
        )

        await interaction.response.send_message(
            f"Exported {len(marked)} marked messages.",
            file=file,
            ephemeral=True,
        )

    """ @awards_group.command(
        name="clear",
        description="Export and clear all marked messages (admin only).",
    )
    @is_admin()
    async def clear(self, interaction: Interaction) -> None:
        marked = self.awards_data.get("marked_messages", {})

        if not marked:
            await interaction.response.send_message(
                "No messages to clear. The awards database is already empty.",
                ephemeral=True,
            )
            return

        export_data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "cleared": True,
            "total_messages": len(marked),
            "messages": list(marked.values()),
        }

        json_str = json.dumps(export_data, indent=4, ensure_ascii=False)
        file = discord.File(
            io.BytesIO(json_str.encode("utf-8")),
            filename=f"awards_cleared_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json",
        )

        count = len(marked)
        self.awards_data["marked_messages"] = {}
        AWARDS_LIST[ENV] = self.awards_data
        JsonHelper.save_json(AWARDS_LIST, "json/awards.json")

        await interaction.response.send_message(
            f"Cleared {count} marked messages. Backup file attached.",
            file=file,
            ephemeral=True,
        ) """

    @awards_group.command(
        name="status",
        description="Show current awards configuration and stats.",
    )
    async def status(self, interaction: Interaction) -> None:
        reaction = self.awards_data.get("reaction")
        marked_count = len(self.awards_data.get("marked_messages", {}))

        if reaction:
            status_msg = (
                f"**Awards Reaction:** {reaction}\n**Marked Messages:** {marked_count}"
            )
        else:
            status_msg = (
                "No awards reaction has been set. "
                "Use `/awards setreaction` to configure one."
            )

        await interaction.response.send_message(status_msg, ephemeral=True)

    ###########################################################################
    # Listeners
    ###########################################################################

    @Cog.listener()
    async def on_raw_reaction_add(
        self, payload: discord.RawReactionActionEvent
    ) -> None:
        try:
            await self._handle_award_reaction(payload)
        except discord.DiscordServerError:
            self.bot._log.warning("Discord 503 error in awards on_raw_reaction_add")

    async def _handle_award_reaction(
        self, payload: discord.RawReactionActionEvent
    ) -> None:
        award_reaction = self.awards_data.get("reaction")
        if not award_reaction:
            return

        if self.bot.user and payload.user_id == self.bot.user.id:
            return

        emoji_str = str(payload.emoji)
        if emoji_str != award_reaction:
            return

        message_id_str = str(payload.message_id)

        if message_id_str in self.awards_data.get("marked_messages", {}):
            return

        if payload.guild_id is None:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        channel = guild.get_channel(payload.channel_id)
        if not channel or not isinstance(channel, discord.TextChannel):
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        message_link = (
            f"https://discord.com/channels/{guild.id}/{channel.id}/{message.id}"
        )

        attachments = (
            [att.url for att in message.attachments] if message.attachments else []
        )

        marked_data = {
            "message_id": str(message.id),
            "channel_id": str(channel.id),
            "channel_name": channel.name,
            "author_id": str(message.author.id),
            "author_name": message.author.display_name,
            "author_username": str(message.author),
            "content": message.content,
            "message_link": message_link,
            "attachments": attachments,
            "marked_at": datetime.now(timezone.utc).isoformat(),
            "marked_by_id": str(payload.user_id),
            "original_timestamp": message.created_at.isoformat(),
        }

        if "marked_messages" not in self.awards_data:
            self.awards_data["marked_messages"] = {}

        self.awards_data["marked_messages"][message_id_str] = marked_data
        AWARDS_LIST[ENV] = self.awards_data
        JsonHelper.save_json(AWARDS_LIST, "json/awards.json")

        self.bot._log.info(
            f"Message {message.id} marked for awards by user {payload.user_id}"
        )
