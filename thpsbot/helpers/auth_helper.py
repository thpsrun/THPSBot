from typing import TYPE_CHECKING

from discord import Interaction, Member
from discord.app_commands import CheckFailure, check

if TYPE_CHECKING:
    from main import THPSBot


def is_admin():
    """Restricts commands to requiring to be in an admin or moderator role. Use for sub-commands."""

    @check
    async def predicate(interaction: Interaction):
        bot: "THPSBot" = interaction.client
        if interaction.user == interaction.guild.owner:
            return True

        for role in interaction.user.roles:
            if role.id in list(bot.roles.get("admin", {}).values()):
                return True

        raise CheckFailure()

    return predicate


async def is_admin_user(user: Member, bot: "THPSBot") -> bool:
    """Returns True if the user is the owner or has an admin/mod role."""
    if user == user.guild.owner:
        return True

    for role in user.roles:
        if role.id in list(bot.roles.get("admin", {}).values()):
            return True

    return False
