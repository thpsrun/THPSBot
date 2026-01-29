from typing import TYPE_CHECKING

import discord
from discord import Interaction, app_commands
from discord.ext.commands import Cog

from thpsbot.helpers.auth_helper import is_admin
from thpsbot.helpers.config_helper import ENV, GUILD_ID, REACTIONS_LIST, ROLES_LIST
from thpsbot.helpers.json_helper import JsonHelper

if TYPE_CHECKING:
    from thpsbot.main import THPSBot


async def setup(bot: "THPSBot"):
    await bot.add_cog(RoleCog(bot))


async def teardown(bot: "THPSBot"):
    await bot.remove_cog(name="Roles")  # type: ignore


class RoleSelectDropdown(discord.ui.Select):
    def __init__(
        self,
        options: list[discord.SelectOption],
    ) -> None:
        super().__init__(
            custom_id="role_select",
            placeholder="Select a role...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: Interaction) -> None:
        if interaction.guild is None or not isinstance(
            interaction.user, discord.Member
        ):
            await interaction.response.send_message(
                "This can only be used in a server.",
                ephemeral=True,
            )
            return

        role_id = int(self.values[0])
        role = interaction.guild.get_role(role_id)
        if role is None:
            await interaction.response.send_message(
                "That role no longer exists. Please contact an admin.",
                ephemeral=True,
            )
            return

        member = interaction.user
        if role in member.roles:
            await member.remove_roles(role)
            await interaction.response.send_message(
                f"Removed **{role.name}**.",
                ephemeral=True,
            )
        else:
            await member.add_roles(role)
            await interaction.response.send_message(
                f"Added **{role.name}**.",
                ephemeral=True,
            )


class RoleSelectView(discord.ui.View):
    def __init__(
        self,
        options: list[discord.SelectOption],
    ) -> None:
        super().__init__(timeout=None)
        self.add_item(RoleSelectDropdown(options))


class RoleCog(
    Cog,
    name="Roles",
    description="Manages role assignment via dropdown menus.",
):
    def __init__(self, bot: "THPSBot") -> None:
        self.bot = bot
        self.role_config: dict = REACTIONS_LIST[ENV]

    async def cog_load(self) -> None:
        self.bot.tree.add_command(
            self.role_group,
            guild=discord.Object(id=GUILD_ID),
            override=True,
        )

        if self.role_config.get("message_id") and self.role_config.get("options"):
            view = self._build_view()
            self.bot.add_view(
                view,
                message_id=int(self.role_config["message_id"]),
            )

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(
            self.role_group.name,
            guild=discord.Object(id=GUILD_ID),
        )

    def _build_view(self) -> RoleSelectView:
        select_options = [
            discord.SelectOption(
                label=opt["label"],
                emoji=opt.get("emoji"),
                value=str(opt["role_id"]),
            )
            for opt in self.role_config["options"]
        ]
        return RoleSelectView(select_options)

    def _save_config(self) -> None:
        REACTIONS_LIST[ENV] = self.role_config
        JsonHelper.save_json(REACTIONS_LIST, "json/reactions.json")

    async def _update_message(self) -> None:
        channel_id = self.role_config.get("channel_id")
        message_id = self.role_config.get("message_id")
        if not channel_id or not message_id:
            return

        channel = self.bot.get_channel(int(channel_id))
        if channel is None or not isinstance(channel, discord.TextChannel):
            self.role_config["message_id"] = None
            self.role_config["channel_id"] = None
            self._save_config()
            self.bot._log.warning(
                "Role-select channel %s no longer accessible; cleared stored IDs.",
                channel_id,
            )
            return

        try:
            message = await channel.fetch_message(int(message_id))
        except discord.NotFound:
            self.role_config["message_id"] = None
            self.role_config["channel_id"] = None
            self._save_config()
            self.bot._log.warning(
                "Role-select message %s not found; cleared stored IDs.",
                message_id,
            )
            return

        if self.role_config["options"]:
            view = self._build_view()
            await message.edit(view=view)
        else:
            await message.edit(view=None)

    ###########################################################################
    # role_group Commands
    ###########################################################################
    role_group = app_commands.Group(
        name="role", description="Manage self-assignable roles."
    )

    @role_group.command(
        name="add",
        description="Add a role option to the role-select dropdown.",
    )
    @app_commands.describe(
        label="Display name for the option (e.g. 'THPS1').",
        emoji="Emoji shown next to the option.",
        role="Discord role to assign when selected.",
    )
    @is_admin()
    async def role_add(
        self,
        interaction: Interaction,
        label: str,
        emoji: str,
        role: discord.Role,
    ) -> None:
        options: list[dict] = self.role_config.get("options", [])

        if len(options) >= 25:
            await interaction.response.send_message(
                "Cannot add more than 25 options.",
                ephemeral=True,
            )
            return

        for opt in options:
            if opt["label"].lower() == label.lower():
                await interaction.response.send_message(
                    f'An option with label "{label}" already exists.',
                    ephemeral=True,
                )
                return

        options.append(
            {
                "label": label,
                "emoji": emoji,
                "role_id": role.id,
            }
        )
        self.role_config["options"] = options
        self._save_config()

        if self.role_config.get("message_id"):
            await self._update_message()

        await interaction.response.send_message(
            f"Added **{label}** ({emoji}) → {role.mention}.",
            ephemeral=True,
        )

    @role_group.command(
        name="remove",
        description="Remove a role option from the role-select dropdown.",
    )
    @app_commands.describe(
        label="Label of the option to remove.",
    )
    @is_admin()
    async def role_remove(
        self,
        interaction: Interaction,
        label: str,
    ) -> None:
        options: list[dict] = self.role_config.get("options", [])
        original_len = len(options)

        self.role_config["options"] = [
            opt for opt in options if opt["label"].lower() != label.lower()
        ]

        if len(self.role_config["options"]) == original_len:
            await interaction.response.send_message(
                f'No option with label "{label}" was found.',
                ephemeral=True,
            )
            return

        self._save_config()

        if self.role_config.get("message_id"):
            await self._update_message()

        await interaction.response.send_message(
            f"Removed **{label}**.",
            ephemeral=True,
        )

    @role_group.command(
        name="send",
        description="Send or refresh the role-select message in a channel.",
    )
    @app_commands.describe(
        channel="Channel to send the role-select message to.",
        text="Text displayed above the dropdown.",
    )
    @is_admin()
    async def role_send(
        self,
        interaction: Interaction,
        channel: discord.TextChannel,
        text: str = "**Select a role from the dropdown below:**",
    ) -> None:
        options: list[dict] = self.role_config.get("options", [])
        if not options:
            await interaction.response.send_message(
                "No role options configured. Use `/role add` first.",
                ephemeral=True,
            )
            return

        view = self._build_view()

        existing_message_id = self.role_config.get("message_id")
        existing_channel_id = self.role_config.get("channel_id")

        if existing_message_id and existing_channel_id:
            existing_channel = self.bot.get_channel(int(existing_channel_id))
            if (
                existing_channel is not None
                and isinstance(existing_channel, discord.TextChannel)
                and existing_channel.id == channel.id
            ):
                try:
                    message = await existing_channel.fetch_message(
                        int(existing_message_id),
                    )
                    await message.edit(content=text, view=view)
                    await interaction.response.send_message(
                        f"Role-select message updated in {channel.mention}.",
                        ephemeral=True,
                    )
                    return
                except discord.NotFound:
                    pass

        message = await channel.send(
            content=text,
            view=view,
        )

        self.role_config["message_id"] = str(message.id)
        self.role_config["channel_id"] = str(channel.id)
        self._save_config()

        await interaction.response.send_message(
            f"Role-select message sent to {channel.mention}.",
            ephemeral=True,
        )

    @role_group.command(
        name="list",
        description="List all configured role options.",
    )
    @is_admin()
    async def role_list(
        self,
        interaction: Interaction,
    ) -> None:
        options: list[dict] = self.role_config.get("options", [])
        if not options:
            await interaction.response.send_message(
                "No role options configured.",
                ephemeral=True,
            )
            return

        guild = interaction.guild
        lines: list[str] = []
        for i, opt in enumerate(options, start=1):
            role_name = f"<@&{opt['role_id']}>" if guild else str(opt["role_id"])
            emoji = opt.get("emoji", "")
            lines.append(f"{i}. {emoji} {opt['label']} --> {role_name}")

        await interaction.response.send_message(
            "\n".join(lines),
            ephemeral=True,
        )

    ###########################################################################
    # mod_group Commands
    ###########################################################################
    mod_group = app_commands.Group(
        name="mod",
        description="Manage game mod-ping roles.",
        parent=role_group,
    )

    def _save_roles(self) -> None:
        ROLES_LIST[ENV] = self.bot.roles
        JsonHelper.save_json(ROLES_LIST, "json/roles.json")

    @mod_group.command(
        name="add",
        description="Add a game mod-ping role.",
    )
    @app_commands.describe(
        slug="Game slug from speedrun.com/thps.run (e.g. 'thps1').",
        role="Discord role to associate with this game.",
    )
    @is_admin()
    async def mod_add(
        self,
        interaction: Interaction,
        slug: str,
        role: discord.Role,
    ) -> None:
        slug = slug.upper()
        mods: dict[str, int] = self.bot.roles.get("mods", {})

        if slug in mods:
            await interaction.response.send_message(
                f"**{slug}** already exists (role <@&{mods[slug]}>).",
                ephemeral=True,
            )
            return

        mods[slug] = role.id
        self.bot.roles["mods"] = mods
        self._save_roles()

        await interaction.response.send_message(
            f"Added **{slug}** → {role.mention}.",
            ephemeral=True,
        )

    @mod_group.command(
        name="remove",
        description="Remove a game mod-ping role.",
    )
    @app_commands.describe(
        slug="Game slug to remove.",
    )
    @is_admin()
    async def mod_remove(
        self,
        interaction: Interaction,
        slug: str,
    ) -> None:
        slug = slug.upper()
        mods: dict[str, int] = self.bot.roles.get("mods", {})

        if slug not in mods:
            await interaction.response.send_message(
                f"No mod role found for **{slug}**.",
                ephemeral=True,
            )
            return

        del mods[slug]
        self.bot.roles["mods"] = mods
        self._save_roles()

        await interaction.response.send_message(
            f"Removed **{slug}**.",
            ephemeral=True,
        )

    @mod_remove.autocomplete("slug")
    async def mod_remove_slug_autocomplete(
        self,
        interaction: Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        mods: dict[str, int] = self.bot.roles.get("mods", {})
        return [
            app_commands.Choice(name=slug, value=slug)
            for slug in mods
            if current.upper() in slug.upper()
        ][:25]
