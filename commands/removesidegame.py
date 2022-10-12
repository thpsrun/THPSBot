import json

def main(arg):
    loadjson = open("./json/sidegames.json", "r")
    sidegames = json.load(loadjson)

    for key in sidegames["Games"]:
        try: username = key["gameabbr"]
        except KeyError: return 1

        if username.casefold() == arg.casefold():
            del key["gameid"]
            del key["gamename"]
            del key["gameabbr"]
            loadjson.close()
            loadjson = open("./json/sidegames.json", "w")

            sidegames = json.dumps(sidegames)
            sidegames = sidegames.replace(', {}', '').replace('{}','')

            loadjson.write(sidegames)
            loadjson.close()
            return 0