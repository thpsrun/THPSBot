import aiosqlite

async def main(arg):
    async with aiosqlite.connect("dbs/streamlist.db") as connect:
        cursor = await connect.cursor()
        await cursor.execute("SELECT text FROM exemptions WHERE UPPER(text) LIKE ?", (arg.upper(),))        
        
        results = await cursor.fetchone()
        if(results != None):
            await cursor.execute("DELETE FROM exemptions WHERE text=?", (results[0],))
            await connect.commit()
            return 0
        else:
            return 1