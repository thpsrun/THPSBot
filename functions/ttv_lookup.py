import time,traceback,aiosqlite
from dbs import config
from twitchAPI.twitch import Twitch

async def main(streamlist):
    returnedjson = []

    async def gamesdb():
        async with aiosqlite.connect("dbs/ttvids.db") as connect:
            cursor = await connect.cursor()
            await cursor.execute("SELECT text FROM games")
            ttvids = await cursor.fetchall()
            ttvids = [row[0] for row in ttvids]
            return ttvids

    ttvids = await gamesdb()
    
    try:
        twitch = await Twitch(config.ttv["id"],config.ttv["token"])
        async for stream in twitch.get_streams(game_id=ttvids):
            if len(stream.title) != 0:
                for user in streamlist:
                    if stream.user_login.casefold() in user.casefold():
                        streamtnail = stream.thumbnail_url.replace("{width}","1280").replace("{height}","720") + "?rand=" + str(int(time.time()))        
                        async for userexport in twitch.get_users(logins=stream.user_login):
                            returnedjson.append({"title":stream.title,"gname":stream.game_name,"tnail":streamtnail,"user":userexport.display_name,"pfp":userexport.profile_image_url})

        if returnedjson != 0:
            return returnedjson
        else:
            return 0
    except UnboundLocalError:
        print("--- Server error occurred... Skipping round...")
        return str(traceback.print_exc()) 