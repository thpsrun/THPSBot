import aiosqlite

async def main(type,arg):
    async with aiosqlite.connect("dbs/online.db") as connect:
        cursor = await connect.cursor()
        if type == 0:
            await cursor.execute("SELECT * FROM twitch")
            online = await cursor.fetchall()
            if len(online) == 0:
                return ["NA"]
            else:
                return online
        elif type == 1:
            await cursor.execute("INSERT INTO twitch VALUES (?,?,?)", (arg))
        elif type == 2:
            await cursor.execute(f"DELETE FROM twitch WHERE username = '{arg}'")
        elif type == 3:
            await cursor.execute("SELECT * FROM youtube")
            online = await cursor.fetchall()
            if len(online) == 0:
                return ["NA"]
            else:
                return online
        elif type == 4:
            await cursor.execute("INSERT INTO youtube VALUES (?,?,?)", (arg))
        elif type == 5:
            await cursor.execute(f"DELETE FROM youtube WHERE username = '{arg}'")

        await connect.commit()