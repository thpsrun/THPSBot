import os

from discord import Interaction, app_commands


async def get_pfp_filenames(
    interaction: Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    pfps = os.listdir("pfps/")
    matches = [f for f in pfps if current.lower() in f.lower()]
    return [app_commands.Choice(name=m, value=m) for m in matches[:25]]
