from time import sleep
import requests,datetime,traceback
from requests.structures import CaseInsensitiveDict

def execute(lookup,type):    
    try:
        if type == 0: runid = lookup["id"]
        else: runid = lookup

        print("--- [SRCOM] Found {0}.".format(runid))

        try:
            runinfo = requests.get("https://speedrun.com/api/v1/runs/{0}?embed=game,category,platform,players,level".format(runid)).json()["data"]
        except KeyError:
            return str(traceback.print_exc())

        runlink = runinfo["weblink"]
        gameid = runinfo["game"]["data"]["id"]
        gameabbr = runinfo["game"]["data"]["abbreviation"]
        gamename = runinfo["game"]["data"]["names"]["international"]
        gamecover = runinfo["game"]["data"]["assets"]["cover-large"]["uri"]

        playerid = runinfo["players"]["data"][0]["id"]
        playername = runinfo["players"]["data"][0]["names"]["international"]
        playerpic = runinfo["players"]["data"][0]["assets"]["image"]["uri"]

        rundate = runinfo["submitted"]

        if runinfo["players"]["data"][0]["twitch"] != None:
            playerttv = runinfo["players"]["data"][0]["twitch"]["uri"].replace("https://www.twitch.tv/","")

            specialcharacters = "!@#$%^&*()-+?=,<>/"
            if any(c in specialcharacters for c in playerttv):
                playerttv = 0
        else:
            playerttv = 0

        catid = runinfo["category"]["data"]["id"]
        catname = runinfo["category"]["data"]["name"]

        platformname = runinfo["platform"]["data"]["name"]
        runcomment = runinfo["comment"]
        variables = runinfo["values"]

        if len(runinfo["level"]["data"]) == 0:
            if len(variables) == 0:
                subcatname = 0
                lbline = 0
            else:
                lbline = ""
                subcatname = ""
                for key in variables:
                    keyvar = variables.get(key)
                    varlookupstr = "var-{0}={1}&".format(key,keyvar)

                    varlookup = requests.get("https://speedrun.com/api/v1/variables/{0}".format(key)).json()["data"]["values"]["values"][keyvar]["label"]

                    subcatname += "{0}, ".format(varlookup)

                    lbline += varlookupstr
            
                lbline = lbline[:-1]
                subcatname = subcatname[:-2]
            
            subcatname = "(" + str(subcatname) + ")"

            lvlid = "NoILFound"
            lvlname = 0
        else:
            lvlid = runinfo["level"]["data"]["id"]
            lvlname = runinfo["level"]["data"]["name"]
            subcatname = "(" + lvlname + ")"
            lbline = 0
            
        runtime = runinfo["times"]["primary_t"]
        if runtime == runinfo["times"]["realtime_t"]: runtype = "(RTA)"
        elif runtime == runinfo["times"]["realtime_noloads_t"]: runtype = "(RTA w/o Loads)"
        else: runtype = "(IGT)"
        runtime = str(datetime.timedelta(seconds=runtime))
        if "." in runtime: runtime = runtime[:-3]

        attempts = 0
        while attempts < 2:
            try:
                if lvlid != "NoILFound":
                    wrsecs = requests.get("https://speedrun.com/api/v1/leaderboards/{0}/level/{1}/{2}".format(gameid,lvlid,catid)).json()["data"]["runs"][0]["run"]["times"]["primary_t"]
                else:
                    wrsecs = requests.get("https://speedrun.com/api/v1/leaderboards/{0}/category/{1}?{2}".format(gameid,catid,lbline)).json()["data"]["runs"][0]["run"]["times"]["primary_t"]
            except IndexError:
                attempts += 1
                sleep(1)
        
        if attempts == 2: wrsecs = "NoWR"

        if type == 1:
            offset = 0
            playerruns = len(requests.get("https://speedrun.com/api/v1/runs?game={0}&user={1}&status=verified&max=200".format(gameid,playerid)).json()["data"])
            
            while playerruns % 200 == 0:
                offset += 200
                lookup = len(requests.get("https://speedrun.com/api/v1/runs?game={0}&user={1}&status=verified&offset={2}&max=200".format(gameid,playerid,offset)).json()["data"])
                if lookup > 1:
                    playerruns += lookup
                else:
                    break
        else:
            playerruns = 0

        export = {
            "id":runid,
            "pid":playerid,
            "pname":playername,
            "pfp":playerpic,
            "ptotalruns":playerruns,
            "pttv":playerttv,
            "gid":gameid,
            "gname":gamename,
            "gcover":gamecover,
            "abbr":gameabbr,
            "link":runlink,
            "cid":catid,
            "cname":catname,
            "subcatname":subcatname,
            "lvlid":lvlid,
            "lvlname":lvlname,
            "platform":platformname,
            "runcomment":runcomment,
            "date":rundate,
            "time":runtime,
            "runtype":runtype,
            "variables":variables,
            "lbline":lbline,
            "wrsecs":wrsecs
        }    
        return export
    except:
        return str(traceback.print_exc())