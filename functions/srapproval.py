import requests,math,traceback
from functions import srlookup
from math import exp

def execute(lookup):
    try:
        print("--- [SRCOM] Evaluating submission approval.")
        runinfo = srlookup.execute(lookup,1)
        
        if runinfo["lvlid"] == "NoILFound":
            lb = requests.get("https://speedrun.com/api/v1/leaderboards/{0}/category/{1}?{2}".format(runinfo["gid"],runinfo["cid"],runinfo["lbline"])).json()["data"]["runs"]
        else:
            lb = requests.get("https://speedrun.com/api/v1/leaderboards/{0}/level/{1}/{2}".format(runinfo["gid"],runinfo["lvlid"],runinfo["cid"])).json()["data"]["runs"]
        

        wr = lb[0]
        wrsec = wr["run"]["times"]["primary_t"]
        runtotal = len(lb)

        for run in lb:
            if runinfo["id"] == run["run"]["id"]:
                place = run["place"]
                pbsec = run["run"]["times"]["primary_t"]
                verifydate = run["status"]["verify-date"]

                ratio = 4.8284 * (wrsec/pbsec)
                if runinfo["gname"] == "THPS - Category Extensions":
                    points = math.trunc(0.008 * exp(ratio) * 10)
                elif runinfo["lvlid"] != "NoILFound":
                    points = math.trunc(0.008 * exp(ratio) * 100)
                else:
                    points = math.trunc(0.008 * exp(ratio) * 1000)
                
                pass

        try: return place,points,wrsec,pbsec,runinfo,runtotal,verifydate
        except UnboundLocalError: return 0,0,0,0,0,0
    except:
        return str(traceback.print_exc())