import asyncio
from typing import TYPE_CHECKING

import discord
from discord import Interaction, app_commands
from discord.ext.commands import Cog

from thpsbot.helpers.config_helper import ENV, GUILD_ID, REACTIONS_LIST
from thpsbot.helpers.json_helper import JsonHelper

if TYPE_CHECKING:
    from main import THPSBot


async def setup(bot: "THPSBot"):
    await bot.add_cog(RoleCog(bot))


async def teardown(bot: "THPSBot"):
    await bot.remove_cog(name="Roles")


class RoleCog(Cog, name="Roles", description="Manages THPSBot's reaction messages."):
    def __init__(self, bot: "THPSBot") -> None:
        self.bot = bot
        self.reactions_list: dict[dict, str] = REACTIONS_LIST[ENV]

    async def cog_load(self) -> None:
        self.bot.tree.add_command(
            self.reaction_group,
            guild=discord.Object(id=GUILD_ID),
            override=True,
        )

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(
            self.reaction_group,
            type=app_commands.Group,
            guild=discord.Object(id=GUILD_ID),
        )

    ###########################################################################
    # reaction_group Commands
    ###########################################################################
    reaction_group = app_commands.Group(
        name="reaction", description="Modify how roles are assigned."
    )

    @reaction_group.command(
        name="message",
        description="Set or removes reactions and roles from a specific message.",
    )
    @app_commands.describe(
        action="Set or remove the reaction from the message ID given",
        message="Message that will receive the emoji reaction.",
        emoji="Emoticon that will be used to represent a role as a recaction.",
        role="@Discord Role you want to use associated with the emoticon.",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="set", value="set"),
            app_commands.Choice(name="remove", value="remove"),
        ]
    )
    async def reactions(
        self,
        interaction: Interaction,
        action: app_commands.Choice[str],
        message: str,
        emoji: str | None,
        role: discord.Role | None,
    ) -> None:
        """Set or removes reactions and roles from a specific message."""
        if action.value == "set":
            if not emoji or not role:
                await interaction.response.send_message(
                    "The emoji and role parameters are required to set a reaction.",
                    ephemeral=True,
                )
                return

            message_id = await interaction.channel.fetch_message(int(message))
            await asyncio.sleep(0.5)
            await message_id.add_reaction(emoji)

            try:
                self.reactions_list[message]
            except (KeyError, TypeError):
                self.reactions_list[message] = {"reactions": {}}

            self.reactions_list[message]["reactions"][emoji] = role.id
            REACTIONS_LIST[ENV] = self.reactions_list

            JsonHelper.save_json(REACTIONS_LIST, "json/reactions.json")

            await interaction.response.send_message(
                f"{message} has received {emoji} as a reaction; when pressed, it will give {role}!",
                ephemeral=True,
            )
        else:
            try:
                message_id = await interaction.channel.fetch_message(int(message))

                if emoji or role:
                    if emoji:
                        await message_id.clear_reaction(emoji)

                    if role:
                        for emoji_find, role_id in self.reactions_list[message][
                            "reactions"
                        ].items():
                            if role_id == role.id:
                                emoji = emoji_find
                                await message_id.clear_reaction(emoji)
                                break
                        else:
                            raise app_commands.errors.CommandInvokeError

                    self.reactions_list[message]["reactions"].pop(emoji, None)
                    if len(self.reactions_list[message]["reactions"]) == 0:
                        self.reactions_list.pop(message, None)
                else:
                    for emoji, role in self.reactions_list[message][
                        "reactions"
                    ].items():
                        await message_id.clear_reaction(emoji)

                    self.reactions_list.pop(message, None)

                REACTIONS_LIST[ENV] = self.reactions_list
                JsonHelper.save_json(REACTIONS_LIST, "json/reactions.json")

                await interaction.response.send_message(
                    f"{message} successfully modified!", ephemeral=True
                )
            except (KeyError, TypeError) as e:
                await interaction.response.send_message(
                    f"Message ID {message} was not in the reactions list or an error occurred.",
                    ephemeral=True,
                )
                self.bot._log.exception("REACTION_REMOVE_EXCEPTION", exc_info=e)

    ###########################################################################
    # Listeners
    ###########################################################################

    @Cog.listener()
    async def on_raw_reaction_add(
        self, payload: discord.RawReactionActionEvent
    ) -> None:
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        emoji_str = str(payload.emoji)
        message_str = str(payload.message_id)

        if message_str not in self.reactions_list:
            return

        role_id = self.reactions_list[message_str]["reactions"].get(emoji_str)
        if role_id is None:
            await message.clear_reaction(payload.emoji)
            return

        role = guild.get_role(role_id)
        if not role:
            return

        member = guild.get_member(payload.user_id)
        if member.bot or member.id == self.bot.user.id:
            return
        elif not member:
            member = await guild.fetch_member(payload.user_id)

        if role in member.roles:
            await member.remove_roles(role)

            try:
                await member.send(
                    f"{role.name} role was removed from your profile successfully in {guild.name}."
                )
            except Exception:
                pass

            await asyncio.sleep(0.5)
        else:
            await member.add_roles(role)
            try:
                await member.send(
                    f"{role.name} role was added to your profile successfully in {guild.name}."
                )
            except discord.Forbidden:
                pass

            await asyncio.sleep(0.5)

        await message.remove_reaction(payload.emoji, member)
        await message.add_reaction(payload.emoji)

    @Cog.listener()
    async def on_raw_reaction_clear(
        self, payload: discord.RawReactionClearEvent
    ) -> None:
        message_id = str(payload.message_id)
        if message_id in self.reactions_list:
            self.bot._log.warning(
                f"Someone cleared all reactions from {payload.message_id}. Readding reactions..."
            )

            guild = self.bot.get_guild(payload.guild_id)
            channel = guild.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            await message.clear_reactions()

            for reaction, _ in self.reactions_list[message_id]["reactions"].items():
                await message.add_reaction(reaction)
