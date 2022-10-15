import json,requests

def main(arg):
    loadjson = open("./json/sidegames.json", "r")
    sidegames = json.load(loadjson)

    for key in sidegames["Games"]:
        try: gameid = key["gameabbr"]
        except KeyError: break

        if gameid.casefold() == arg.casefold(): return 1

    try: game = requests.get("https://speedrun.com/api/v1/games/{0}".format(arg)).json()["data"]
    except KeyError: return 2

    sidegames["Games"].append({"gameid":game["id"],"gamename":game["names"]["international"],"gameabbr":game["abbreviation"]})

    loadjson.close()
    loadjson = open("./json/sidegames.json", "w")
    loadjson.write(json.dumps(sidegames))
    loadjson.close()

    return 0