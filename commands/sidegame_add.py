import aiosqlite,aiohttp

async def main(arg):
    async with aiosqlite.connect("dbs/sidegames.db") as connect:
        cursor = await connect.cursor()
        await cursor.execute("SELECT abbr FROM sidegames WHERE UPPER(abbr) LIKE ?", (arg.upper(),))

        if(cursor.fetchone() != None):
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http:/speedrun.com/api/v1/games/{arg}") as r:
                    if r.status == 200:
                        json_data = await r.json()
                        json_data = json_data["data"]
                        await cursor.execute("INSERT INTO sidegames VALUES (?,?,?)", (json_data["id"], json_data["names"]["international"], json_data["abbreviation"]))
                        await connect.commit()
                        return 0
                    else:
                        return 2
        else:
            return 1