import json

def main(arg):
    loadjson = open("./json/streamlist.json", "r")
    streamlist = json.load(loadjson)
    loadjson.close()

    for key in streamlist["Streams"]["Twitch"]:
        username = key["username"]

        if username.casefold() == arg.casefold():
            return 0

    return 1