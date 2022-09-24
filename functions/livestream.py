import configparser,traceback,time
from twitchAPI.twitch import Twitch

def execute(username):
    config = configparser.ConfigParser()
    config.read("./config.ini")
    configtwitch = config["Twitch"]

    ttvid = configtwitch["ttvid"]
    ttvtoken = configtwitch["ttvtoken"]

    try: 
        twitch = Twitch(ttvid,ttvtoken)
        export = twitch.get_streams(user_login=username)["data"]

        if len(export) != 0:
            try:
                for i in export:
                    streamgame  = i["game_name"]
                    if not streamgame in configtwitch["ttvgames"]:
                        return
                    elif "Pokémon" in streamgame:
                        return
                    elif len(streamgame) == 0:
                        return

                    streamtitle = i["title"]
                    streamtnail = i["thumbnail_url"].replace("{width}","1280").replace("{height}","720") + "?rand=" + str(int(time.time()))

                export1 = twitch.get_users(logins=username)["data"]

                for i in export1:
                    streamname  = i["display_name"]
                    streampfp   = i["profile_image_url"]

                return [streamname,streampfp,streamtitle,streamgame,streamtnail]        
            except UnboundLocalError:
                return str(traceback.print_exc())
    except: 
        print("--- Server error occurred... Skipping round...")
        return 0