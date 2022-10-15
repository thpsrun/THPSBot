import json

def main(arg):
    loadjson = open("./json/streamlist.json", "r")
    streamlist = json.load(loadjson)

    for key in streamlist["Streams"]["Twitch"]:
        try: username = key["username"]
        except: return 1

        if username.casefold() == arg.casefold():
            del key["username"]
            loadjson.close()
            loadjson = open("./json/streamlist.json", "w")

            streamlist = json.dumps(streamlist)
            streamlist = streamlist.replace(', {}', '')

            loadjson.write(streamlist)
            loadjson.close()
            return 0