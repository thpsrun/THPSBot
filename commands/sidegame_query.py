import aiosqlite

async def main(arg):
    async with aiosqlite.connect("dbs/sidegames.db") as connect:
        cursor  = await connect.cursor()
        await cursor.execute("SELECT query FROM sidegames WHERE UPPER(query) LIKE ?", (arg.upper(),))        
        if(await cursor.fetchone() != None):
            return 0
        else:
            return 1