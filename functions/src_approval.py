import math
from functions import src_api_call,src_lookup
from math import exp

async def main(lookup):
    print("--- [SRCOM] Evaluating submission approval.")
    runinfo = await src_lookup.main(1,lookup)
    
    if runinfo["lvlid"] == "NoILFound":
        lb = await src_api_call.main(f"https://speedrun.com/api/v1/leaderboards/{runinfo['gid']}/category/{runinfo['cid']}?{runinfo['lbline']}")
        lb = lb["runs"]
    else:
        lb = await src_api_call.main(f"https://speedrun.com/api/v1/leaderboards/{runinfo['gid']}/level/{runinfo['lvlid']}/{runinfo['cid']}")
        lb = lb["runs"]
    runtotal = len(lb)

    if len(lb) > 0:
        for run in lb:
            if runinfo["id"] == run["run"]["id"]:
                place = run["place"]
                try: verifydate = run["run"]["status"]["verify-date"]
                except KeyError: verifydate = 0

                if runinfo["wrsecs"] == "NoWR": ratio = 4.8284 * (runinfo["pbsecs"]/runinfo["pbsecs"])
                else: ratio = 4.8284 * (runinfo["wrsecs"]/runinfo["pbsecs"])
                    
                if "Category Extensions" in runinfo["gname"]:
                    points = math.trunc(0.008 * exp(ratio) * 10)
                    if points > 10: points = 10
                elif runinfo["lvlid"] != "NoILFound":
                    points = math.trunc(0.008 * exp(ratio) * 100)
                    if points > 100: points = 100
                else:
                    points = math.trunc(0.008 * exp(ratio) * 1000)
                    if points > 1000: points = 1000
                
                pass
        
                return place,points,runinfo["wrsecs"],runinfo["pbsecs"],runinfo,runtotal,verifydate
    else:
        return 0,0,0,0,0,0,0