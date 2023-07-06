import aiosqlite

async def main(arg):
    async with aiosqlite.connect("dbs/streamlist.db") as connect:
        cursor = await connect.cursor()
        await cursor.execute("SELECT text FROM exemptions WHERE UPPER(text) LIKE ?", (arg.upper(),)) 

        if(await cursor.fetchone() == None):
            await cursor.execute("INSERT INTO exemptions VALUES (?,?)",(None, arg))
            await connect.commit()
            return 0
        else:
            return 1