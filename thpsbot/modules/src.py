from typing import TYPE_CHECKING

from discord.ext import tasks
from discord.ext.commands import Cog

from thpsbot.helpers.aiohttp_helper import AIOHTTPHelper
from thpsbot.helpers.config_helper import THPS_RUN_API

if TYPE_CHECKING:
    from main import THPSBot


async def setup(bot: "THPSBot"):
    await bot.add_cog(SRCCog(bot))


async def teardown(bot: "THPSBot"):
    await bot.remove_cog(name="SRC")


class SRCCog(Cog, name="SRC", description="Automates checks with Speedrun.com's API."):
    def __init__(self, bot: "THPSBot") -> None:
        self.bot = bot
        self.local_src: list = []

    async def cog_load(self) -> None:
        self.src_check.start()

    async def cog_unload(self) -> None:
        self.src_check.cancel()

    @tasks.loop(minutes=1)
    async def src_check(self) -> None:
        game_list = await AIOHTTPHelper.get(
            url=f"{THPS_RUN_API}/games/all",
            headers=self.bot.thpsrun_header,
        )

        for game in game_list.data:
            src_check = await AIOHTTPHelper.get(
                url=f"https://speedrun.com/api/v1/runs?status=new&game={game['id']}",
                headers=self.bot.thpsrun_header,
            )

            if not src_check.ok:
                continue

            run_ids = [run["id"] for run in src_check.data["data"]]
            for run_id in run_ids:
                if run_id not in self.local_src:
                    await AIOHTTPHelper.post(
                        url=f"{THPS_RUN_API}/runs/{run_id}",
                        headers=self.bot.thpsrun_header,
                        data=None,
                    )
                    self.local_src.append(run_id)

        runs_list = await AIOHTTPHelper.get(
            url=f"{THPS_RUN_API}/runs/all?query=status"
            + "&embed=players,game,platform,record,platform",
            headers=self.bot.thpsrun_header,
        )

        if not src_check.ok:
            return

        for run in runs_list.data["new_runs"]:
            run_check = await AIOHTTPHelper.get(
                url=f"https://speedrun.com/api/v1/runs/{run['id']}",
                headers=None,
            )

            if run_check.status == 404:
                await AIOHTTPHelper.post(
                    url=f"{THPS_RUN_API}/runs/{run['id']}",
                    headers=self.bot.thpsrun_header,
                    data=None,
                )
                self.local_src.remove(run["id"])
            elif run_check.ok:
                if run_check.data["data"]["status"]["status"] != "new":
                    await AIOHTTPHelper.post(
                        url=f"{THPS_RUN_API}/runs/{run['id']}",
                        headers=self.bot.thpsrun_header,
                        data=None,
                    )
                    self.local_src.remove(run["id"])
            else:
                continue
