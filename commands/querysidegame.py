import json

def main():
    loadjson = open("./json/sidegames.json", "r")
    sidegames = json.load(loadjson)
    loadjson.close()

    output = ""
    for key in sidegames["Games"]:
        output = output + key["gamename"] + ", "

    output = output[:-2]
    return output