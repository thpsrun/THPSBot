import random
from datetime import datetime, timezone

import discord
from discord import Embed
from dotenv import load_dotenv

from thpsbot.helpers.config_helper import BOT, DEFAULT_IMG, THPS_RUN_API

THPS_RUN = THPS_RUN_API.replace("/api", "")
load_dotenv()


class EmbedCreator:
    @staticmethod
    def approved_embed(
        title: str,
        subcategory: str,
        url: str,
        player: str,
        player_pfp: str | None,
        placement: int,
        points: float,
        platform: str,
        time: str,
        time_delta: str | None,
        completed_runs: int | None,
        run_type: str,
        description: str | None,
        thumbnail: str | None,
        approval: str,
        obsolete: bool,
    ) -> Embed:
        """After approval, this embed would be ran to display the newly approved run."""
        if player_pfp:
            pfp = THPS_RUN + player_pfp.lstrip("srl")
        else:
            pfp = DEFAULT_IMG

        embed = Embed(
            title=title,
            url=url,
            color=random.randint(0, 0xFFFFFF),
            timestamp=datetime.fromisoformat(approval.replace("Z", "+00:00")),
        )

        embed.set_author(name=player, url=f"{THPS_RUN}/player/{player}", icon_url=pfp)

        if obsolete:
            embed.add_field(name="Placement", value=f"{placement}", inline=True)
            embed.add_field(name="Points", value=f"{points}", inline=True)

        embed.add_field(name="Platform", value=platform, inline=True)
        embed.set_footer(text=BOT)

        embed.description = f"{subcategory}\n Time: {time} ({run_type})"

        if time_delta:
            embed.add_field(name="WR [Delta]", value=time_delta, inline=True)

        if completed_runs:
            embed.add_field(name="Completed Runs", value=completed_runs, inline=True)

        if description:
            embed.add_field(name="Comments", value=description[:1024], inline=False)

        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        return embed

    @staticmethod
    def submission_embed(
        title: str,
        subcategory: str,
        url: str,
        player: str,
        player_pfp: str | None,
        time: str,
        run_type: str,
        thumbnail: str | None,
        submitted: str,
    ) -> Embed:
        """This embed is used to showcase that an embed is in the queue from Speedrun.com."""
        if player_pfp:
            pfp = THPS_RUN + player_pfp.lstrip("srl")
        else:
            pfp = DEFAULT_IMG

        embed = Embed(
            title=title,
            url=url,
            color=random.randint(0, 0xFFFFFF),
            timestamp=datetime.fromisoformat(submitted.replace("Z", "+00:00")),
        )

        embed.set_author(name=player, url=f"{THPS_RUN}/player/{player}", icon_url=pfp)
        embed.set_footer(text=BOT)

        embed.description = f"{subcategory}\n Time: {time} ({run_type})"

        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        return embed

    @staticmethod
    def player_embed(
        player: str,
        nickname: str | None,
        player_pfp: str | None,
        total_points: int,
        main_points: int | None,
        il_points: int | None,
        total_runs: int,
        recent_main_runs: dict[str, dict] | None,
        recent_il_runs: dict[str, dict] | None,
    ) -> Embed:
        """This embed is used to display players from the thps.run API."""
        if nickname:
            title_name = f"{player} ({nickname})"
        else:
            title_name = player

        if player_pfp:
            pfp = THPS_RUN + player_pfp.lstrip("srl")
        else:
            pfp = DEFAULT_IMG

        embed = Embed(
            title=f"{title_name}",
            color=random.randint(0, 0xFFFFFF),
            timestamp=datetime.now(timezone.utc),
        )

        embed.set_author(name=player, url=f"{THPS_RUN}/player/{player}", icon_url=pfp)
        embed.add_field(name="Stats", value="", inline=False)
        embed.add_field(name="Total Points", value=total_points, inline=True)

        if main_points:
            embed.add_field(name="Main Game Points", value=main_points, inline=True)

        if il_points:
            embed.add_field(name="IL Points", value=il_points, inline=True)

        embed.add_field(name="Total Runs", value=total_runs, inline=True)
        embed.set_footer(text=BOT)

        time_key_map = {
            "realtime": "time",
            "realtime_noloads": "timenl",
            "ingame": "timeigt",
        }

        if len(recent_main_runs) > 0:
            embed.add_field(name="Most Recent Main Game Runs", value="", inline=False)

            run_number = 1
            for run in recent_main_runs:
                default_time = run["times"]["defaulttime"]
                time_key = time_key_map.get(default_time)

                game = run["game"]["slug"].upper()
                subcat = run["subcategory"]
                time = run["times"][time_key]
                url = run["meta"]["url"]

                embed.add_field(
                    name=run_number,
                    value=f"[{game} - {subcat} in {time}]({url})",
                    inline=False,
                )

                run_number += 1

        if len(recent_il_runs) > 0:
            embed.add_field(name="Most Recent IL Runs", value="", inline=False)

            run_number = 1
            for run in recent_il_runs:
                default_time = run["times"]["defaulttime"]
                time_key = time_key_map.get(default_time)

                game = run["game"]["slug"].upper()
                subcat = run["subcategory"]
                time = run["times"][time_key]
                url = run["meta"]["url"]

                embed.add_field(
                    name=run_number,
                    value=f"[{game} - {subcat} in {time}]({url})",
                    inline=False,
                )

                run_number += 1

        return embed

    @staticmethod
    def twitch_embed(
        title: str,
        thps_user: str,
        stream_name: str,
        stream_game: str,
        twitch_pfp: str | None,
        thumbnail: str,
        src_username: str,
    ) -> Embed:
        """This embed is used to display currently online livestreams."""
        if not twitch_pfp:
            twitch_pfp = DEFAULT_IMG

        embed = Embed(
            title=title,
            url=f"https://twitch.tv/{stream_name}",
            color=random.randint(0, 0xFFFFFF),
            timestamp=datetime.now(timezone.utc),
        )

        embed.set_author(
            name=f"{stream_name} is online!",
            url=f"https://twitch.tv/{stream_name}",
            icon_url=twitch_pfp,
        )
        embed.add_field(name="Game", value=stream_game, inline=True)
        embed.set_image(url=thumbnail)
        embed.set_footer(text=BOT)

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="Twitch",
                url=f"https://twitch.tv/{stream_name}",
                emoji=discord.PartialEmoji(name="twitch", id=1391866611358629908),
            )
        )

        if "-mar" not in thps_user:
            view.add_item(
                discord.ui.Button(
                    label="Speedrun.com",
                    url=f"https://speedrun.com/{src_username}",
                    emoji=discord.PartialEmoji(name="src", id=1391867987157319882),
                )
            )

            view.add_item(
                discord.ui.Button(
                    label="thps.run",
                    url=f"https://thps.run/player/{src_username}",
                    emoji=discord.PartialEmoji(name="thpsrun", id=1391866542500872382),
                )
            )

        return embed, view

    @staticmethod
    def twitch_offline_embed(
        stream_name: str,
        stream_game: str,
        twitch_pfp: str | None,
        started_at: str,
        archive_video: str | None,
    ) -> Embed:
        """This embed is used to display currently online livestreams."""
        if not twitch_pfp:
            twitch_pfp = DEFAULT_IMG

        secs_uptime = (
            datetime.now(timezone.utc) - datetime.fromisoformat(started_at)
        ).total_seconds()
        hours = int(secs_uptime // 3600)
        minutes = int((secs_uptime % 3600) // 60)

        embed = Embed(
            title=f"{stream_name} is offline!",
            url=f"https://twitch.tv/{stream_name}",
            color=random.randint(0, 0xFFFFFF),
            timestamp=datetime.now(timezone.utc),
        )

        embed.set_author(
            name=stream_name,
            url=f"https://twitch.tv/{stream_name}",
            icon_url=twitch_pfp,
        )
        embed.add_field(name="Game", value=stream_game, inline=True)

        if hours > 0:
            embed.add_field(
                name="Stream Time",
                value=f"{abs(hours)} hours and {abs(minutes)} minutes",
            )
        else:
            embed.add_field(name="Stream Time", value=f"{abs(minutes)} minutes")

        if archive_video:
            embed.description = f"Stream VOD: {archive_video}"

        embed.set_footer(text=BOT)

        return embed
