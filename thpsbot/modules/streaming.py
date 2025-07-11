import asyncio
import time
from typing import TYPE_CHECKING

import discord
from discord import Interaction, app_commands
from discord.ext import tasks
from discord.ext.commands import Cog
from twitchAPI.helper import first
from twitchAPI.twitch import Twitch
from twitchAPI.type import SortMethod, VideoType

from thpsbot.helpers.aiohttp_helper import AIOHTTPHelper
from thpsbot.helpers.config_helper import (
    GUILD_ID,
    LIVE_LIST,
    STREAM_CHANNEL,
    STREAM_OFF_THREAD,
    THPS_RUN_API,
    TTV_ID,
    TTV_TOKEN,
    TTVGAME_IDS,
    TTVGAME_LIST,
)
from thpsbot.helpers.embed_helper import EmbedCreator
from thpsbot.helpers.json_helper import JsonHelper

if TYPE_CHECKING:
    from main import THPSBot


async def setup(bot: "THPSBot"):
    await bot.add_cog(StreamingCog(bot))


async def teardown(bot: "THPSBot"):
    await bot.remove_cog(name="Streaming")


class StreamingCog(
    Cog, name="Streaming", description="Manages THPSBot's stream checks"
):
    def __init__(self, bot: "THPSBot") -> None:
        self.bot = bot
        self.stream_role: int = int(self.bot.roles["admin"]["stream"])
        self.ttv_games: list = TTVGAME_LIST
        self.live: dict[dict, str] = LIVE_LIST

        self.stream_game_lookup: list = TTVGAME_IDS

        self.task_lock = asyncio.Lock()

    async def cog_load(self) -> None:
        self.stream_channel = await self.bot.fetch_channel(STREAM_CHANNEL)
        self.stream_thread = await self.bot.fetch_channel(STREAM_OFF_THREAD)
        self.ttv_client = await Twitch(app_id=TTV_ID, app_secret=TTV_TOKEN)

        self.bot.tree.add_command(
            self.stream_group,
            guild=discord.Object(id=GUILD_ID),
            override=True,
        )

        self.stream_loop.start()

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(
            self.stream_group,
            type=app_commands.Group,
            guild=discord.Object(id=GUILD_ID),
        )
        await self.ttv_client.close()

        self.stream_loop.cancel()

    @tasks.loop(minutes=1)
    async def stream_loop(self) -> None:
        """Checks livestream status of players every minute."""
        async with self.task_lock:
            player_list = await AIOHTTPHelper.get(
                url=f"{THPS_RUN_API}/players/all?query=streams",
                headers=self.bot.thpsrun_header,
            )

            if not player_list.data or not player_list.ok:
                self.bot._log.error("No player data received; is thps.run online?")
                return

            for game_id in self.stream_game_lookup:
                async for stream in self.ttv_client.get_streams(
                    game_id=[game_id], first=100, stream_type="live"
                ):
                    if not stream.title:
                        continue

                    for _, entry in enumerate(player_list.data):
                        if not entry.get("twitch"):
                            continue

                        if (
                            entry.get("twitch").casefold()
                            == stream.user_login.casefold()
                        ):
                            user = await first(
                                self.ttv_client.get_users(logins=stream.user_login)
                            )
                            try:
                                self.live[user.display_name]
                            except (KeyError, TypeError):
                                if (
                                    "NoSRL".casefold()
                                    not in (tag.casefold() for tag in stream.tags)
                                    and entry.get("ex_stream") is False
                                ):
                                    thumbnail = stream.thumbnail_url.replace(
                                        "{width}", "1280"
                                    ).replace("{height}", "720")

                                    e_thumbnail = (
                                        thumbnail + "?rand=" + str(int(time.time()))
                                    )

                                    embed, view = EmbedCreator.twitch_embed(
                                        title=stream.title,
                                        thps_user=entry.get("id"),
                                        stream_name=user.display_name,
                                        stream_game=stream.game_name,
                                        twitch_pfp=user.profile_image_url,
                                        thumbnail=e_thumbnail,
                                        src_username=entry.get("name"),
                                    )

                                    embed_stream = await self.stream_channel.send(
                                        embed=embed, view=view
                                    )
                                    role_msg = await self.stream_channel.send(
                                        f"<@&{self.stream_role}>"
                                    )

                                    self.live.update(
                                        {
                                            f"{user.display_name}": {
                                                "user_id": user.id,
                                                "thpsrun_id": entry.get(
                                                    "id"
                                                ),  # temporary until local done
                                                "src_username": entry.get("name"),
                                                "embed": embed_stream.id,
                                                "role": role_msg.id,
                                                "game": stream.game_name,
                                                "thumbnail": thumbnail,
                                                "pfp": user.profile_image_url,
                                                "started_at": str(stream.started_at),
                                                "check": 0,
                                            }
                                        }
                                    )

            remove_stream = []
            for user, messages in self.live.items():

                stream = await first(self.ttv_client.get_streams(user_login=user))

                if stream is None or stream.game_id not in self.stream_game_lookup:
                    if messages["check"] >= 5:
                        remove_stream.append(user)
                    else:
                        check = messages["check"] + 1
                        self.live[user].update({"check": check})
                else:
                    e_thumbnail = (
                        messages["thumbnail"] + "?rand=" + str(int(time.time()))
                    )

                    embed, view = EmbedCreator.twitch_embed(
                        title=stream.title,
                        thps_user=messages["thpsrun_id"],
                        stream_name=user,
                        stream_game=stream.game_name,
                        twitch_pfp=messages["pfp"],
                        thumbnail=e_thumbnail,
                        src_username=messages["src_username"],
                    )

                    try:
                        embed_stream = await self.stream_channel.fetch_message(
                            messages["embed"]
                        )

                        await embed_stream.edit(embed=embed, view=view)
                    except discord.errors.NotFound:
                        new_embed = await self.stream_channel.send(embed=embed)
                        self.live[user].update({"embed": new_embed.id})

                    self.live[user].update({"check": 0})

            if len(remove_stream) > 0:
                for stream in remove_stream:
                    archive = await first(
                        self.ttv_client.get_videos(
                            user_id=self.live[stream]["user_id"],
                            video_type=VideoType.ARCHIVE,
                            first=1,
                            sort=SortMethod.TIME,
                        )
                    )

                    await self.stream_thread.send(
                        embed=EmbedCreator.twitch_offline_embed(
                            stream_name=stream,
                            stream_game=self.live[stream]["game"],
                            twitch_pfp=self.live[stream]["pfp"],
                            started_at=self.live[stream]["started_at"],
                            archive_video=archive.url if archive else None,
                        )
                    )

                    remove_embed = await self.stream_channel.fetch_message(
                        self.live[stream]["embed"]
                    )
                    remove_role = await self.stream_channel.fetch_message(
                        self.live[stream]["role"]
                    )

                    await remove_embed.delete()
                    await remove_role.delete()
                    self.live.pop(stream, None)

            JsonHelper.save_json(self.live, "json/live.json")

    @tasks.loop(minutes=60)
    async def check_twitch_names(self) -> None:
        """Checks the names in the local JSON file to see if they are real Twitch games."""
        for ttv_game in self.ttv_games:
            async for game in self.ttv_client.get_games(names=[ttv_game]):
                if game.id not in self.stream_game_lookup:
                    self.stream_game_lookup.append(game.id)

        JsonHelper.save_json(self.stream_game_lookup, "json/ttvgame_ids.json")

    @stream_loop.before_loop
    async def before_status_loop(self) -> None:
        """Check messages in the livestream channel before executing."""
        await self.check_twitch_names()

    ###########################################################################
    # stream_group Commands
    ###########################################################################
    stream_group = app_commands.Group(
        name="stream",
        description="Commands related to modifying the behavior of the bot's Twitch components.",
    )

    @stream_group.command(
        name="game",
        description="Modifies the games looked up by THPSBot to the Twitch API.",
    )
    @app_commands.describe(
        action="Add a game to the lookup table",
        name="Name of the game. EXACT MATCH ONLY!",
    )
    @app_commands.choices(action=[app_commands.Choice(name="add", value="add")])
    async def stream_game(
        self, interaction: Interaction, action: app_commands.Choice[str], name: str
    ) -> None:
        """Modifies the games looked up by THPSBot to the Twitch API."""
        await interaction.response.defer(thinking=True, ephemeral=True)

        if action.value == "add":
            if name not in self.ttv_games:
                game = await first(self.ttv_client.get_games(names=name))

                if game.id not in self.stream_game_lookup:
                    self.stream_game_lookup.append(game.id)
                    self.ttv_games.append(game.name)

                    JsonHelper.save_json(
                        self.stream_game_lookup, "json/ttvgame_ids.json"
                    )
                    JsonHelper.save_json(self.ttv_games, "json/ttvgames.json")

                    await interaction.followup.send(
                        f"{name} has been added to the lookup table.", ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"{name} was not added. That game's Twitch ID already exists.",
                        ephemeral=True,
                    )
            else:
                await interaction.followup.send(
                    f"{name} was not added. Did you spell it right? Does the category exist?",
                    ephemeral=True,
                )
