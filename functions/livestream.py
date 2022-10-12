import configparser,time,traceback
from twitchAPI.twitch import Twitch

def execute(streamlist):
    config = configparser.ConfigParser()
    config.read("./config.ini")
    configtwitch = config["Twitch"]
    gameslist = configtwitch["ttvids"]
    gameslist = gameslist.replace("\n","").replace("[","").replace("]","").replace("\"","").split(',')

    ttvid = configtwitch["ttvid"]
    ttvtoken = configtwitch["ttvtoken"]

    returnedjson = []

    try:
        twitch = Twitch(ttvid,ttvtoken)
        export = twitch.get_streams(game_id=gameslist)["data"]

        if len(export) != 0:
            for stream in export:
                for user in streamlist["Streams"]["Twitch"]:
                    if stream["user_login"].casefold() in user["username"].casefold():
                        streamtnail = stream["thumbnail_url"].replace("{width}","1280").replace("{height}","720") + "?rand=" + str(int(time.time()))        
                        userexport = twitch.get_users(logins=stream["user_login"])["data"]

                        returnedjson.append({"title":stream["title"],"gname":stream["game_name"],"tnail":streamtnail,"user":userexport[0]["display_name"],"pfp":userexport[0]["profile_image_url"]})
                        break

            return returnedjson
        else:
            return 0
    except UnboundLocalError:
        print("--- Server error occurred... Skipping round...")
        return str(traceback.print_exc()) 