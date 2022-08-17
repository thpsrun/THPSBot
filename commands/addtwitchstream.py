import json

def main(arg):
    loadjson = open("./json/streamlist.json", "r")
    streamlist = json.load(loadjson)

    for key in streamlist["Streams"]["Twitch"]:
        username = key["username"]

        if username.casefold() == arg.casefold():
            return 1
    
    jsonupdate = {"username":arg.lower()}
    streamlist["Streams"]["Twitch"].append(jsonupdate)

    loadjson.close()
    loadjson = open("./json/streamlist.json", "w")
    loadjson.write(json.dumps(streamlist))
    loadjson.close()

    return 0