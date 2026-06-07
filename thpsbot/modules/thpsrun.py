from typing import TYPE_CHECKING

import discord
from discord import Interaction, app_commands
from discord.ext import tasks
from discord.ext.commands import Cog

from thpsbot.helpers.aiohttp_helper import AIOHTTPHelper
from thpsbot.helpers.auth_helper import is_admin_user
from thpsbot.helpers.config_helper import (
    GUILD_ID,
    PB_WR_CHANNEL,
    SUBMISSION_CHANNEL,
    SUBMISSIONS_LIST,
    THPS_RUN_API,
    THPS_RUN_KEY,
    THPS_RUN_SITE,
)
from thpsbot.helpers.embed_helper import EmbedCreator
from thpsbot.helpers.json_helper import JsonHelper
from thpsbot.helpers.task_helper import TaskHelper
from thpsbot.helpers.thpsrun_helper import THPSRunHelper
from thpsbot.models import (
    PlayerResponse,
    SRCRunsData,
    THPSRunGame,
    THPSRunPlatform,
    THPSRunRuns,
)

if TYPE_CHECKING:
    from thpsbot.main import THPSBot


async def setup(bot: "THPSBot"):
    await bot.add_cog(THPSRunCog(bot))


async def teardown(bot: "THPSBot"):
    await bot.remove_cog(name="THPSRun")  # type: ignore


class THPSRunCog(
    Cog, name="THPSRun", description="Manages THPSBot's integration with thps.run"
):
    submit_channel: discord.TextChannel
    pb_channel: discord.TextChannel

    def __init__(self, bot: "THPSBot") -> None:
        self.bot = bot
        self.thpsrun_header: dict[str, str] = {
            "X-API-Key": THPS_RUN_KEY,
        }
        self.submissions: dict[str, dict] = SUBMISSIONS_LIST

    async def _fetch_player_pfp(
        self,
        run: THPSRunRuns,
    ) -> str | None:
        if not run.players:
            return None

        resp = await AIOHTTPHelper.get(
            url=f"{THPS_RUN_API}/players/{run.players[0].id}",
            headers=self.bot.thpsrun_header,
        )
        if not (resp.ok and isinstance(resp.data, dict)):
            return None

        pfp = (resp.data.get("player") or {}).get("pfp")
        if not pfp:
            return None

        return f"{THPS_RUN_SITE}{pfp}"

    async def cog_load(self) -> None:
        submit_ch = await self.bot.fetch_channel(SUBMISSION_CHANNEL)
        pb_ch = await self.bot.fetch_channel(PB_WR_CHANNEL)

        if not isinstance(submit_ch, discord.TextChannel):
            raise RuntimeError("SUBMISSION_CHANNEL is not a TextChannel")
        if not isinstance(pb_ch, discord.TextChannel):
            raise RuntimeError("PB_WR_CHANNEL is not a TextChannel")

        self.submit_channel = submit_ch
        self.pb_channel = pb_ch

        self.bot.tree.add_command(
            self.thpsrun_group,
            guild=discord.Object(id=GUILD_ID),
            override=True,
        )

        self._check_approval_status.start()
        await AIOHTTPHelper.init_session()

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(
            self.thpsrun_group.name,
            guild=discord.Object(id=GUILD_ID),
        )

        self._check_approval_status.cancel()
        await AIOHTTPHelper.close_session()

    @tasks.loop(seconds=30)
    @TaskHelper.safe_task
    async def _check_approval_status(self):
        await self._approval_status()

    async def _approval_status(self):
        resp = await AIOHTTPHelper.get(
            url=f"{THPS_RUN_API}/runs/all?status=new&embed=game,category,level,platform",
            headers=self.thpsrun_header,
        )
        if resp.ok and isinstance(resp.data, list):
            new_runs = [THPSRunRuns(**raw) for raw in resp.data]
            for run in new_runs:
                try:
                    self.submissions[run.id]
                except (KeyError, TypeError):
                    run_data = THPSRunHelper.get_run_data(run)
                    if run_data is None:
                        continue

                    role_msg_id = None
                    if isinstance(run.game, THPSRunGame):
                        role_id = self.bot.roles.get("mods", {}).get(
                            run.game.slug.upper()
                        )
                        if role_id is not None:
                            role_msg = await self.submit_channel.send(
                                f"<@&{int(role_id)}>"
                            )
                            role_msg_id = role_msg.id

                    warnings = await THPSRunHelper.get_import_issues(self.bot, run.id)
                    player_pfp = await self._fetch_player_pfp(run)

                    board_url = await THPSRunHelper.build_leaderboard_url(self.bot, run)
                    embed, view = EmbedCreator.submission_embed(
                        title=run_data.embed_title,
                        subcategory=run.subcategory,
                        url=run.url,
                        player=run_data.players,
                        player_pfp=player_pfp,
                        time=run_data.time,
                        run_type=run_data.run_type,
                        submitted=run.date,
                        warnings=warnings,
                    )
                    embed_msg = await self.submit_channel.send(
                        embed=embed,
                        view=view,
                    )

                    self.submissions.update(
                        {
                            f"{run.id}": {
                                "submission": embed_msg.id,
                                "role": role_msg_id,
                            }
                        }
                    )
                except Exception as e:
                    self.bot._log.exception(e)

        remove_run = []
        for run_id in self.submissions:
            resp = await AIOHTTPHelper.get(
                url=f"{THPS_RUN_API}/runs/{run_id}?embed=game,category,level,platform",
                headers=self.thpsrun_header,
            )

            if resp.status == 404:
                try:
                    embed_msg = await self.submit_channel.fetch_message(
                        self.submissions[run_id]["submission"]
                    )
                    await embed_msg.delete()
                except discord.NotFound:
                    pass

                if self.submissions[run_id]["role"]:
                    try:
                        role_msg = await self.submit_channel.fetch_message(
                            self.submissions[run_id]["role"]
                        )
                        await role_msg.delete()
                    except discord.NotFound:
                        pass

                remove_run.append(run_id)
                continue

            if not resp.ok or not isinstance(resp.data, dict):
                continue

            run_verify = THPSRunRuns(**resp.data)

            if run_verify.vid_status == "verified":
                run_data = THPSRunHelper.get_run_data(run_verify)

                if run_data:
                    record = await THPSRunHelper.get_record_delta(self.bot, run_verify)
                    if record is None or record.get("record", "x") is None:
                        time_delta: str | None = "No Previous WR"
                    elif record.get("is_record"):
                        time_delta = None
                    else:
                        delta_fmt = THPSRunHelper.format_time(record["delta_secs"])
                        time_delta = f"{record['wr_time']} [+{delta_fmt}]"

                    wr_reign = None
                    if record and record.get("is_record"):
                        wr_reign = await THPSRunHelper.get_wr_reign(
                            self.bot, run_verify
                        )

                    platform_name = (
                        run_verify.platform.name
                        if isinstance(run_verify.platform, THPSRunPlatform)
                        else (run_verify.platform or "Unknown")
                    )
                    player_pfp = await self._fetch_player_pfp(run_verify)

                    board_url = await THPSRunHelper.build_leaderboard_url(
                        self.bot, run_verify
                    )
                    embed, view = EmbedCreator.approved_embed(
                        title=run_data.embed_title,
                        subcategory=run_verify.subcategory or "",
                        url=run_verify.url,
                        player=run_data.players,
                        player_pfp=player_pfp,
                        placement=run_verify.place,
                        points=run_verify.points or 0,
                        platform=platform_name,
                        time=run_data.time,
                        time_delta=time_delta,
                        completed_runs=None,
                        run_type=run_data.run_type,
                        description=run_verify.description,
                        approval=run_verify.v_date,
                        obsolete=run_verify.obsolete,
                        wr_reign=wr_reign,
                        board_url=board_url,
                    )
                    await self.pb_channel.send(
                        embed=embed,
                        view=view,
                    )

                    embed_msg = await self.submit_channel.fetch_message(
                        self.submissions[run_id]["submission"]
                    )
                    await embed_msg.delete()

                    if self.submissions[run_id]["role"]:
                        role_msg = await self.submit_channel.fetch_message(
                            self.submissions[run_id]["role"]
                        )
                        await role_msg.delete()

                    remove_run.append(run_id)
            elif run_verify.vid_status == "rejected":
                embed_msg = await self.submit_channel.fetch_message(
                    self.submissions[run_id]["submission"]
                )
                await embed_msg.delete()

                if self.submissions[run_id]["role"]:
                    role_msg = await self.submit_channel.fetch_message(
                        self.submissions[run_id]["role"]
                    )
                    await role_msg.delete()

                remove_run.append(run_id)
            else:
                continue

        if len(remove_run) > 0:
            for run_id in remove_run:
                self.submissions.pop(run_id)

        JsonHelper.save_json(self.submissions, "json/submissions.json")

    ###########################################################################
    # thpsrun_group Commands
    ###########################################################################
    thpsrun_group = app_commands.Group(
        name="thpsrun", description="Player-related commands from thps.run"
    )

    @thpsrun_group.command(
        name="player",
        description="Show or update information on a player from thps.run.",
    )
    @app_commands.describe(
        action="Show information about a player. Admins can use update to force updates.",
        name="The name (or unique ID) of the player you want to show.",
        nickname="When declared, the player will be given the specified nickname.",
        ex_stream="Used with update for admins; when True, the user is exempted from Twitch checks",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="show", value="show"),
            app_commands.Choice(name="update", value="update"),
        ]
    )
    async def thpsrun_player(
        self,
        interaction: Interaction,
        action: app_commands.Choice[str],
        name: str,
        nickname: str | None,
        ex_stream: bool | None,
    ):
        if action.value == "show":
            resp = await AIOHTTPHelper.get(
                url=f"{THPS_RUN_API}/players/{name}?embed=stats,runs,country",
                headers=self.thpsrun_header,
            )

            if not resp.ok or not isinstance(resp.data, dict):
                await interaction.response.send_message(
                    content="An error occurred looking up that player.",
                    ephemeral=True,
                )
                return

            player_data = PlayerResponse(**resp.data)

            await interaction.response.send_message(
                embed=EmbedCreator.player_embed(
                    player=player_data.player.name,
                    nickname=player_data.player.nickname,
                    player_pfp=player_data.player.pfp,
                    fg_points=(
                        player_data.stats.fg_points if player_data.stats else None
                    ),
                    il_points=(
                        player_data.stats.il_points if player_data.stats else None
                    ),
                    total_runs=(
                        player_data.stats.total_runs if player_data.stats else None
                    ),
                    recent_main_runs=player_data.runs.fg if player_data.runs else None,
                    recent_il_runs=player_data.runs.il if player_data.runs else None,
                )
            )
        else:
            if not await is_admin_user(interaction.user, self.bot):
                raise app_commands.CheckFailure

            if nickname is not None and len(nickname) > 30:
                await interaction.response.send_message(
                    content="The nickname given is greater than 30 characters.",
                    ephemeral=True,
                )
                return

            lookup = await AIOHTTPHelper.get(
                url=f"{THPS_RUN_API}/players/{name}",
                headers=self.thpsrun_header,
            )

            if not lookup.ok or not isinstance(lookup.data, dict):
                await interaction.response.send_message(
                    content="An error occurred looking up that player.",
                    ephemeral=True,
                )
                return

            player_id = lookup.data["id"]

            response = await AIOHTTPHelper.put(
                url=f"{THPS_RUN_API}/players/{player_id}",
                headers=self.thpsrun_header,
                data={"nickname": nickname, "ex_stream": ex_stream},
            )

            if response.ok:
                await interaction.response.send_message(
                    content=f"{name} was successfully updated!",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    content="An unknown error occurred.",
                    ephemeral=True,
                )
                self.bot._log.exception(
                    f"update_player: {response.status} {response.data}"
                )

    @thpsrun_group.command(
        name="run", description="Show or import a run from or to the thps.run API."
    )
    @app_commands.describe(
        action="Show a run from the thps.run API. Admins can force import a run to the API.",
        url="The unique ID of a run from SRC OR the full URL of the run itself.",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="show", value="show"),
            app_commands.Choice(name="import", value="import"),
        ]
    )
    async def thpsrun_run(
        self,
        interaction: Interaction,
        action: app_commands.Choice[str],
        url: str,
    ) -> None:
        if action.value == "show":
            if "speedrun.com" in url:
                run_id = THPSRunHelper.get_run_id(url.lower())
                if run_id is None:
                    await interaction.followup.send(
                        content="Invalid Speedrun.com URL format.",
                        ephemeral=True,
                    )
                    return
                url = run_id

            resp = await AIOHTTPHelper.get(
                url=f"{THPS_RUN_API}/runs/{url}?embed=game,category,level,platform",
                headers=self.thpsrun_header,
            )

            if not resp.ok or not isinstance(resp.data, dict):
                await interaction.response.send_message(
                    content=f"An error occurred looking up {url}.",
                    ephemeral=True,
                )
                return

            run = THPSRunRuns(**resp.data)
            run_data = THPSRunHelper.get_run_data(run)

            if run.vid_status == "verified":
                if run_data:
                    platform_name = (
                        run.platform.name
                        if isinstance(run.platform, THPSRunPlatform)
                        else (run.platform or "Unknown")
                    )

                    record = await THPSRunHelper.get_record_delta(self.bot, run)
                    if record is None or record.get("record", "x") is None:
                        time_delta: str | None = "No Previous WR"
                    elif record.get("is_record"):
                        time_delta = None
                    else:
                        delta_fmt = THPSRunHelper.format_time(record["delta_secs"])
                        time_delta = f"{record['wr_time']} [+{delta_fmt}]"

                    player_pfp = await self._fetch_player_pfp(run)

                    board_url = await THPSRunHelper.build_leaderboard_url(self.bot, run)
                    embed, view = EmbedCreator.approved_embed(
                        title=run_data.embed_title,
                        subcategory=run.subcategory,
                        url=run.url,
                        player=run_data.players,
                        player_pfp=player_pfp,
                        placement=run.place,
                        points=run.points or 0,
                        platform=platform_name,
                        time=run_data.time,
                        time_delta=time_delta,
                        completed_runs=None,
                        run_type=run_data.run_type,
                        description=run.description,
                        approval=run.v_date,
                        obsolete=run.obsolete,
                        board_url=board_url,
                    )
                    await interaction.response.send_message(
                        embed=embed,
                        view=view,
                    )
            else:
                await interaction.response.send_message(
                    content="Run is still awaiting verification.",
                    ephemeral=True,
                )
        else:
            if not await is_admin_user(interaction.user, self.bot):
                raise app_commands.CheckFailure

            await interaction.response.defer(thinking=True, ephemeral=True)

            run_id = THPSRunHelper.get_run_id(url.lower())
            if not run_id:
                await interaction.followup.send(
                    content="Invalid Speedrun.com URL format.",
                    ephemeral=True,
                )
                return

            src_resp = await AIOHTTPHelper.get(
                url=f"https://www.speedrun.com/api/v1/runs/{run_id}",
                headers=self.bot.src_header,
            )
            if not src_resp.ok or not isinstance(src_resp.data, dict):
                await interaction.followup.send(
                    content="Could not fetch run from speedrun.com.",
                    ephemeral=True,
                )
                return
            src = SRCRunsData(**src_resp.data).data

            body: dict = {
                "id": src.id,
                "game_id": src.game,
                "category_id": src.category,
                "level_id": src.level,
                "runtype": "il" if src.level else "main",
                "player_ids": [p.id for p in src.players if p.id],
                "platform_id": src.system.platform,
                "emulated": src.system.emulated,
                "url": src.weblink,
                "video": (
                    src.videos.links[0].uri if src.videos and src.videos.links else None
                ),
                "time_secs": src.times.realtime_t,
                "timenl_secs": src.times.realtime_noloads_t,
                "timeigt_secs": src.times.ingame_t,
                "date": src.date,
                "v_date": src.status.verify_date,
                "vid_status": (
                    src.status.status
                    if src.status.status in ("verified", "new", "rejected", "review")
                    else "new"
                ),
                "place": 999,
                "approver_id": src.status.examiner,
                "variable_values": src.values,
                "description": src.comment,
            }

            post_run = await AIOHTTPHelper.post(
                url=f"{THPS_RUN_API}/runs/",
                headers=self.thpsrun_header,
                data=body,
            )

            if post_run.ok:
                await interaction.followup.send(
                    content=f"Run `{src.id}` successfully imported to thps.run!\n"
                    + f"Use `/thpsrun run show {src.id}` to view it.",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    content=f"Failed to import run to thps.run: {post_run.data}",
                    ephemeral=True,
                )
