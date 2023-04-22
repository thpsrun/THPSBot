import aiosqlite

async def main(type,tuple):
    async with aiosqlite.connect("dbs/submissions.db") as connect:
        cursor = await connect.cursor()
        if type == 0:
            await cursor.execute("SELECT * FROM maingames")
            submissions = await cursor.fetchall()
            return submissions
        elif type == 1:
            await cursor.execute("INSERT INTO maingames VALUES (?,?,?,?)", tuple)
        elif type == 2:
            await cursor.execute(f"DELETE FROM maingames WHERE id = '{tuple}'")
        elif type == 3:
            await cursor.execute("SELECT * FROM sidegames")
            submissions = await cursor.fetchall()
            return submissions
        elif type == 4:
            await cursor.execute("INSERT INTO sidegames VALUES (?,?)", tuple)
        elif type == 5:
            await cursor.execute(f"DELETE FROM sidegames WHERE id = '{tuple}'")

        await connect.commit()