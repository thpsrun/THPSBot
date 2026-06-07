import random
from datetime import datetime, timezone

import discord
from discord import Embed
from dotenv import load_dotenv

from thpsbot.helpers.config_helper import (
    BOT,
    DEFAULT_IMG,
    THPS_RUN_SITE,
    TTV_TIMEOUT,
)
from thpsbot.helpers.thpsrun_helper import THPSRunHelper
from thpsbot.models import PlayerRunInline

SRC_EMOJI = discord.PartialEmoji(name="src", id=1391867987157319882)
THPSRUN_EMOJI = discord.PartialEmoji(name="thpsrun", id=1391866542500872382)

THPS_RUN = THPS_RUN_SITE
load_dotenv()


def _pfp_icon(
    player_pfp: str | None,
) -> str:
    if not player_pfp:
        return DEFAULT_IMG
    if player_pfp.startswith("http"):
        return player_pfp
    return f"{THPS_RUN_SITE}{player_pfp}"


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
        approval: str | None,
        obsolete: bool,
        wr_reign: str | None = None,
        board_url: str | None = None,
    ) -> tuple[Embed, discord.ui.View]:
        pfp = _pfp_icon(player_pfp)

        embed = Embed(
            title=title,
            url=board_url or url,
            color=random.randint(0, 0xFFFFFF),
        )
        if approval:
            embed.timestamp = datetime.fromisoformat(approval.replace("Z", "+00:00"))

        embed.set_author(name=player, url=f"{THPS_RUN}/player/{player}", icon_url=pfp)

        if not obsolete:
            embed.add_field(name="Placement", value=f"{placement}", inline=True)
            embed.add_field(name="Points", value=f"{points}", inline=True)

        embed.add_field(name="Platform", value=platform, inline=True)
        embed.set_footer(text=BOT)

        embed.description = f"{subcategory}\nTime: {time} ({run_type})"

        if wr_reign:
            embed.description += f"\n{wr_reign}"

        if time_delta and placement > 1:
            embed.add_field(name="WR [Delta]", value=time_delta, inline=True)

        if completed_runs:
            embed.add_field(name="Completed Runs", value=completed_runs, inline=True)

        if description:
            embed.add_field(name="Comments", value=description[:1024], inline=False)

        view = discord.ui.View()
        if board_url:
            view.add_item(
                discord.ui.Button(
                    label="thps.run",
                    url=board_url,
                    emoji=THPSRUN_EMOJI,
                )
            )
        view.add_item(
            discord.ui.Button(
                label="Speedrun.com",
                url=url,
                emoji=SRC_EMOJI,
            )
        )

        return embed, view

    @staticmethod
    def submission_embed(
        title: str,
        subcategory: str,
        url: str,
        player: str,
        player_pfp: str | None,
        time: str,
        run_type: str,
        submitted: str | None,
        warnings: list | None,
    ) -> tuple[Embed, discord.ui.View]:
        pfp = _pfp_icon(player_pfp)

        embed = Embed(
            title=title,
            color=random.randint(0, 0xFFFFFF),
        )

        if submitted:
            embed.timestamp = datetime.fromisoformat(submitted.replace("Z", "+00:00"))

        embed.set_author(name=player, url=f"{THPS_RUN}/player/{player}", icon_url=pfp)

        embed.set_footer(text=BOT)

        embed.description = f"{subcategory}\nTime: {time} ({run_type})"

        if warnings:
            for warning in warnings:
                embed.add_field(
                    name="Warning",
                    value=warning,
                    inline=False,
                )

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="Submissions",
                url="https://thps.run/submissions",
                emoji=THPSRUN_EMOJI,
            )
        )
        view.add_item(
            discord.ui.Button(
                label="SRC Hub",
                url=url,
                emoji=SRC_EMOJI,
            )
        )

        return embed, view

    @staticmethod
    def player_embed(
        player: str,
        nickname: str | None,
        player_pfp: str | None,
        fg_points: float | None,
        il_points: float | None,
        total_runs: int | None,
        recent_main_runs: list[PlayerRunInline] | None,
        recent_il_runs: list[PlayerRunInline] | None,
    ) -> Embed:
        if nickname:
            title_name = f"{player} ({nickname}) Statistics"
        else:
            title_name = f"{player} Statistics"

        pfp = _pfp_icon(player_pfp)

        embed = Embed(
            title=f"{title_name}",
            color=random.randint(0, 0xFFFFFF),
            timestamp=datetime.now(timezone.utc),
        )

        embed.set_author(name=player, url=f"{THPS_RUN}/player/{player}", icon_url=pfp)

        if fg_points:
            embed.add_field(name="Main Game Points", value=fg_points, inline=True)

        if il_points:
            embed.add_field(name="IL Points", value=il_points, inline=True)

        embed.add_field(name="Total Runs", value=total_runs or 0, inline=True)
        embed.set_footer(text=BOT)

        def _render(
            runs: list[PlayerRunInline],
            header: str,
        ) -> None:
            if not runs:
                return
            embed.add_field(name=header, value="", inline=False)
            for index, run in enumerate(runs, start=1):
                game = (run.game.slug or "").upper() if run.game else ""
                if game == "THPS34":
                    game = "THPS3+4"
                elif game == "THPS12":
                    game = "THPS1+2"
                subcat = run.subcategory or ""
                label = f"{game} - {subcat} in {run.time}"
                board = THPSRunHelper.build_leaderboard_url_inline(run)
                if board and run.url:
                    line = f"{index}. [{label}]({board}) ([SRC]({run.url}))"
                elif board:
                    line = f"{index}. [{label}]({board})"
                elif run.url:
                    line = f"{index}. [{label}]({run.url})"
                else:
                    line = f"{index}. {label}"
                embed.add_field(
                    name="",
                    value=line,
                    inline=False,
                )

        _render(recent_main_runs or [], "Most Recent Main Game Runs")
        _render(recent_il_runs or [], "Most Recent IL Runs")

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
    ) -> tuple[Embed, discord.ui.View]:
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

        # This is a temporary measure added so marathons are displayed differently.
        # If the username ends with "-mar" (e.g. "GamesDoneQuick-mar"), then they will not be given
        # additional buttons. These two buttons are to link to the user's SRC and thps.run profiles.
        if "-mar" not in thps_user:
            view.add_item(
                discord.ui.Button(
                    label="Speedrun.com",
                    url=f"https://speedrun.com/{src_username}",
                    emoji=SRC_EMOJI,
                )
            )

            view.add_item(
                discord.ui.Button(
                    label="thps.run",
                    url=f"https://thps.run/player/{src_username}",
                    emoji=THPSRUN_EMOJI,
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
        if not twitch_pfp:
            twitch_pfp = DEFAULT_IMG

        # This section is to convert the uptime to a proper format to display on the VOD embed.
        secs_uptime = (
            datetime.now(timezone.utc) - datetime.fromisoformat(started_at)
        ).total_seconds() - (TTV_TIMEOUT * 60)
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
