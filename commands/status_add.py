import aiosqlite

async def main(arg):
    async with aiosqlite.connect("dbs/statusmsg.db") as connect:
        cursor = await connect.cursor()
        await cursor.execute("SELECT text FROM games WHERE UPPER(text) LIKE ?", (arg.upper(),)) 

        if(await cursor.fetchone() == None):
            await cursor.execute("INSERT INTO games VALUES (?,?)",(None, arg))
            await connect.commit()
            return 0
        else:
            return 1