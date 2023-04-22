import aiosqlite

async def main(arg):
    async with aiosqlite.connect("dbs/sidegames.db") as connect:
        cursor = await connect.cursor()
        await cursor.execute("SELECT gameid FROM sidegames WHERE UPPER(abbr) LIKE ?", (arg.upper(),))        
        
        results = cursor.fetchone()
        if(results != None):
            await cursor.execute("DELETE FROM sidegames WHERE gameid='?'", (results[0],))
            await connect.commit()
            return 0
        else:
            return 1