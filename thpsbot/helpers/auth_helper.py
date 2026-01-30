from typing import TYPE_CHECKING

from discord import Interaction, Member, User
from discord.app_commands import CheckFailure, check

if TYPE_CHECKING:
    from thpsbot.main import THPSBot


def is_admin():
    @check
    async def predicate(
        interaction: Interaction,
    ) -> bool:
        bot: "THPSBot" = interaction.client  # type: ignore

        if interaction.guild is None:
            raise CheckFailure("This command must be used in a guild.")

        user = interaction.user
        if not isinstance(user, Member):
            raise CheckFailure("Could not verify user permissions.")

        if user == interaction.guild.owner:
            return True

        for role in user.roles:
            if role.id in list(bot.roles.get("admin", {}).values()):
                return True

        raise CheckFailure()

    return predicate


async def is_admin_user(
    user: Member | User,
    bot: "THPSBot",
) -> bool:
    if not isinstance(user, Member):
        return False

    if user.guild.owner and user == user.guild.owner:
        return True

    for role in user.roles:
        if role.id in list(bot.roles.get("admin", {}).values()):
            return True

    return False
