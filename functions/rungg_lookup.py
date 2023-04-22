import aiohttp

async def main(arg):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://therun.gg/api/live") as r:
            if r.status == 200:
                returnedjson = []
                gg_data = await r.json()

                for index, data in enumerate(gg_data):
                    if data["user"].casefold() == arg.casefold():
                        gg_index = index
                        break
                    else:
                        gg_index = -1

                try:
                    if gg_index >= 0:
                        run = gg_data[gg_index]
                        if run["currentSplitIndex"] > 0:
                            lsplit = run["splits"][run["currentSplitIndex"] -1]
                            try:
                                lsplit_ms  = (lsplit["pbSplitTime"] - lsplit["splitTime"]) / 1000
                                lsplit_abs = abs(lsplit_ms)
                                lsplit_sec = int(lsplit_abs % 60)
                                lsplit_min = int(lsplit_abs // 60)
                                lsplit_time = '{}{:02d}:{:02d}'.format("+" if lsplit_ms < 0 else "-", lsplit_min, lsplit_sec)
                            except:
                                lsplit_ms  = "-"

                            lsplit_name = lsplit["name"]
                        else:
                            lsplit_name = False
                            lsplit_time = False

                        returnedjson.append({
                            "game":run["game"],
                            "category":run["category"],
                            "hasReset":run["hasReset"],
                            "lastSplitName":lsplit_name,
                            "lastSplitTime":lsplit_time,
                            "currentSplit":run["splits"][run["currentSplitIndex"]]["name"]
                        })
                    else:
                        returnedjson = []
                except:
                    returnedjson = []
                return returnedjson