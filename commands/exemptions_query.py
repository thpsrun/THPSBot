import aiosqlite

async def main(arg):
    async with aiosqlite.connect("dbs/streamlist.db") as connect:
        cursor  = await connect.cursor()
        await cursor.execute("SELECT text FROM exemptions WHERE UPPER(text) LIKE ?", (arg.upper(),))        
        
        query = await cursor.fetchone()
        if(query != None):
            return 0
        else:
            return 1