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
            await cursor.execute("INSERT INTO twitch VALUES (?,?,?,?)", (arg))
        elif type == 2:
            await cursor.execute("DELETE FROM twitch WHERE username = ?", (arg,))
        elif type == 3:
            await cursor.execute("UPDATE twitch SET checks = ? WHERE username = ?", (arg[1], arg[0]))

        elif type == 4:
            await cursor.execute("SELECT * FROM youtube")
            online = await cursor.fetchall()
            if len(online) == 0:
                return ["NA"]
            else:
                return online
        elif type == 5:
            await cursor.execute("INSERT INTO youtube VALUES (?,?,?,?)", (arg))
        elif type == 6:
            await cursor.execute("DELETE FROM youtube WHERE username = ?", (arg,))
        elif type == 7:
            await cursor.execute("UPDATE youtube SET checks = ? WHERE username = ?", (arg[1], arg[0]))

        await connect.commit()