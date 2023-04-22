import aiosqlite

async def main(type,arg):
    async with aiosqlite.connect("dbs/tonys.db") as connect:
        cursor = await connect.cursor()
        if type == 0:
            await cursor.execute("SELECT * FROM tonys2023 WHERE msgid=?", (arg[0],))
            result = await cursor.fetchone()
            if not result:
                await cursor.execute("INSERT INTO tonys2023 VALUES (?,?,?,?,?)", (arg))
        elif type == 1:
            await cursor.execute(f"DELETE FROM tonys2023 WHERE msgid = '{arg}'")

        await connect.commit()