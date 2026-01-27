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
)
from thpsbot.helpers.embed_helper import EmbedCreator
from thpsbot.helpers.json_helper import JsonHelper
from thpsbot.helpers.task_helper import TaskHelper
from thpsbot.helpers.thpsrun_helper import THPSRunHelper
from thpsbot.models.thpsrun_api import THPSRunPBs, THPSRunRuns

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
            "Authorization": f"Api-Key {THPS_RUN_KEY}"
        }
        self.submissions: dict[str, dict] = SUBMISSIONS_LIST

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

        self.check_approval_status.start()
        await AIOHTTPHelper.init_session()

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(
            self.thpsrun_group.name,
            guild=discord.Object(id=GUILD_ID),
        )

        self.check_approval_status.cancel()
        await AIOHTTPHelper.close_session()

    @tasks.loop(seconds=30)
    @TaskHelper.safe_task
    async def check_approval_status(self):
        """Checks the status of speedruns from thps.run every 30 seconds."""
        await self._check_approval_status_impl()

    async def _check_approval_status_impl(self):
        """Implementation of check_approval_status."""
        get_runs = await AIOHTTPHelper.get(
            url=f"{THPS_RUN_API}/runs/all?query=status"
            + "&embed=players,game,platform,record,platform",
            headers=self.thpsrun_header,
        )

        if get_runs.ok and get_runs.data:
            for run in get_runs.data["new_runs"]:
                run = THPSRunRuns.model_validate(run)
                try:
                    self.submissions[run.id]
                except (KeyError, TypeError):
                    embed_data = THPSRunHelper.get_run_data(run)

                    try:
                        role_id = int(self.bot.roles["mods"][run.game.slug.upper()])
                        role_msg = await self.submit_channel.send(f"<@&{role_id}>")
                        role_msg_id = role_msg.id
                    except Exception:
                        role_msg_id = None

                    if embed_data:
                        embed_msg = await self.submit_channel.send(
                            embed=EmbedCreator.submission_embed(
                                title=embed_data.embed_title,
                                subcategory=run.subcategory,
                                url=run.meta.url,
                                player=embed_data.players,
                                player_pfp=embed_data.player_pfp,
                                time=embed_data.time,
                                run_type=embed_data.run_type,
                                thumbnail=run.game.boxart,
                                submitted=run.date,
                                warnings=embed_data.warnings,
                            )
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
        for run in self.submissions:
            run_verify = await AIOHTTPHelper.get(
                url=f"{THPS_RUN_API}/runs/{run}?embed=players,game,platform,record,platform",
                headers=self.thpsrun_header,
            )

            if run_verify.ok and run_verify.data:
                run_verify = THPSRunRuns.model_validate(run_verify.data)
                if run_verify.status.vid_status == "verified":
                    embed_data = THPSRunHelper.get_run_data(run_verify)

                    if embed_data:
                        if isinstance(run_verify.players, list):
                            completed_runs = run_verify.players[0].stats.total_runs
                        else:
                            completed_runs = run_verify.players.stats.total_runs

                        await self.pb_channel.send(
                            embed=EmbedCreator.approved_embed(
                                title=embed_data.embed_title,
                                subcategory=run_verify.subcategory,
                                url=run_verify.meta.url,
                                player=embed_data.players,
                                player_pfp=embed_data.player_pfp,
                                placement=run_verify.place,
                                lb_count=run_verify.lb_count,
                                points=run_verify.meta.points,
                                platform=run_verify.system.platform.name,
                                time=embed_data.time,
                                time_delta=embed_data.delta,
                                completed_runs=completed_runs,
                                run_type=embed_data.run_type,
                                description=run_verify.description,
                                thumbnail=run_verify.game.boxart,
                                approval=run_verify.status.v_date,
                                obsolete=run_verify.status.obsolete,
                            )
                        )

                        embed_msg = await self.submit_channel.fetch_message(
                            self.submissions[run]["submission"]
                        )
                        await embed_msg.delete()

                        if self.submissions[run]["role"]:
                            role_msg = await self.submit_channel.fetch_message(
                                self.submissions[run]["role"]
                            )
                            await role_msg.delete()

                        remove_run.append(run)

                        if embed_data.warnings:
                            await self.submit_channel.send(
                                content=(
                                    "The following submission has warnings.\n"
                                    f"**[Submission Link]({run_verify.meta.url}) -- Warnings: **"
                                    f"{' | '.join(embed_data.warnings)} \n"
                                    "Once fixed on SRC, a Discord Mod or Admin needs to run: \n"
                                    f"`/thpsrun run import {run_verify.meta.url}`"
                                    "*Remove embed once approved or if a false positive.*"
                                ),
                            )
                elif run_verify.status.vid_status == "rejected":
                    embed_msg = await self.submit_channel.fetch_message(
                        self.submissions[run]["submission"]
                    )
                    await embed_msg.delete()

                    if self.submissions[run]["role"]:
                        role_msg = await self.submit_channel.fetch_message(
                            self.submissions[run]["role"]
                        )
                        await role_msg.delete()

                    remove_run.append(run)
                else:
                    continue

        if len(remove_run) > 0:
            for run in remove_run:
                self.submissions.pop(run)

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
        """Show or update information on a player from thps.run."""
        if action.value == "show":
            get_player = await AIOHTTPHelper.get(
                url=f"{THPS_RUN_API}/players/{name}/pbs?embed=games",
                headers=self.thpsrun_header,
            )

            if get_player.ok and get_player.data:
                player_data = THPSRunPBs.model_validate(get_player.data)
                main_runs = None
                il_runs = None
                if player_data.main_runs:
                    main_runs = player_data.main_runs[:3]

                if player_data.il_runs:
                    il_runs = player_data.il_runs[:3]

                await interaction.response.send_message(
                    embed=EmbedCreator.player_embed(
                        player=player_data.name,
                        nickname=player_data.nickname,
                        player_pfp=player_data.pfp,
                        total_points=player_data.stats.total_pts,
                        main_points=player_data.stats.main_pts,
                        il_points=player_data.stats.il_pts,
                        total_runs=player_data.stats.total_runs,
                        recent_main_runs=main_runs,
                        recent_il_runs=il_runs,
                    )
                )
            else:
                await interaction.response.send_message(
                    content="An error occurred looking up that player.",
                    ephemeral=True,
                )
        else:
            if not await is_admin_user(interaction.user, self.bot):
                raise app_commands.CheckFailure

            data = {}
            if nickname is not None:
                if len(nickname) > 30:
                    await interaction.response.send_message(
                        content="The nickname given is greater than 30 characters.",
                        ephemeral=True,
                    )
                    return

                data.update({"nickname": f"{nickname}"})

            if ex_stream is not None:
                data.update({"ex_stream": ex_stream})

            response = await AIOHTTPHelper.put(
                url=f"{THPS_RUN_API}/players/{name}",
                headers=self.thpsrun_header,
                data=data,
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
        """Show or import a run from or to the thps.run API."""
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

            get_run = await AIOHTTPHelper.get(
                url=f"{THPS_RUN_API}/runs/{url}?embed=game,players,record,platform",
                headers=self.thpsrun_header,
            )

            if get_run.ok and get_run.data:
                run_data = THPSRunRuns.model_validate(get_run.data)

                if run_data.status.vid_status == "verified":
                    embed_data = THPSRunHelper.get_run_data(run_data)

                    if isinstance(run_data.players, list):
                        completed_runs = run_data.players[0].stats.total_runs
                    else:
                        completed_runs = run_data.players.stats.total_runs

                    if embed_data:
                        await interaction.response.send_message(
                            embed=EmbedCreator.approved_embed(
                                title=embed_data.embed_title,
                                subcategory=run_data.subcategory,
                                url=run_data.meta.url,
                                player=embed_data.players,
                                player_pfp=embed_data.player_pfp,
                                placement=run_data.place,
                                lb_count=run_data.lb_count,
                                points=run_data.meta.points,
                                platform=run_data.system.platform.name,
                                time=embed_data.time,
                                time_delta=embed_data.delta,
                                completed_runs=completed_runs,
                                run_type=embed_data.run_type,
                                description=run_data.description,
                                thumbnail=run_data.game.boxart,
                                approval=run_data.status.v_date,
                                obsolete=run_data.status.obsolete,
                            )
                        )
                else:
                    await interaction.response.send_message(
                        content="Run is still awaiting verification.",
                        ephemeral=True,
                    )
            else:
                await interaction.response.send_message(
                    content=f"An error occurred looking up {url}.",
                    ephemeral=True,
                )
        else:
            if not await is_admin_user(interaction.user, self.bot):
                raise app_commands.CheckFailure

            await interaction.response.defer(thinking=True, ephemeral=True)

            if "speedrun.com" in url:
                run_id = THPSRunHelper.get_run_id(url.lower())
                if run_id is None:
                    await interaction.followup.send(
                        content="Invalid Speedrun.com URL format.",
                        ephemeral=True,
                    )
                    return
                url = run_id

            post_run = await AIOHTTPHelper.post(
                url=f"{THPS_RUN_API}/runs/{url}",
                headers=self.thpsrun_header,
                data=None,
            )

            if post_run.ok:
                await interaction.followup.send(
                    content="Run successfully submitted to the thps.run API!\n"
                    + f"Use `/run show {url}`to view it!",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    content="Failed to submit the run to thps.run API.",
                    ephemeral=True,
                )
