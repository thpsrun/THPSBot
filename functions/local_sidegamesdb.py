import aiosqlite

async def main():
    async with aiosqlite.connect("dbs/sidegames.db") as connect:
        cursor = await connect.cursor()
        await cursor.execute("SELECT gameid FROM sidegames")
        sidegames = await cursor.fetchall()
        sidegames = [row[0].casefold() for row in sidegames]
        return sidegames