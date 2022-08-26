from ast import NotIn
import discord,configparser,traceback,json,random,datetime,requests,time
from commands import addtwitchstream,querystream,removetwitchstream,addsidegame,removesidegame,querysidegame
from functions import livestream,srlookup,srapproval
from discord.ext import tasks,commands

config = configparser.ConfigParser()
config.read("./config.ini")
configdiscord = config["Discord"]

intents = discord.Intents.default()
client = commands.Bot(command_prefix=configdiscord["prefix"], intents=intents, help_command=None)

@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))
    await change_status()
    if not start_livestream.is_running():
        start_livestream.start()

    if not change_status.is_running():
        change_status.start()

    if not start_srcom.is_running():
        start_srcom.start()

    if not start_side_srcom.is_running():
        start_side_srcom.start()

@client.command()
@commands.cooldown(1, 10, commands.BucketType.user)
async def ping(ctx):
    if ctx.channel.name == "livestreams" or ctx.channel.name == "mods":
        await ctx.send("Pong!")

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def addstream(ctx,arg):
    errorchannel = await client.fetch_channel(int(configdiscord["admin"]))

    if ctx.channel.name == "livestreams" or ctx.channel.name == "mods":
        try:
            check = addtwitchstream.main(arg)
            if check == 0:
                await ctx.send('{0} was added to the stream list.'.format(arg))
            elif check == 1:
                await ctx.send('{0} was already in the stream list.'.format(arg))
        except:
            errormsg = str(traceback.print_exc())
            await errorchannel.send(errormsg)
            await ctx.send('An error occurred when adding {0}.'.format(arg))

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def removestream(ctx,arg):
    errorchannel = await client.fetch_channel(int(configdiscord["admin"]))

    if ctx.channel.name == "livestreams" or ctx.channel.name == "mods":
        try:
            check = removetwitchstream.main(arg)
            if check == 0:
                await ctx.send('{0} was removed to the stream list.'.format(arg))
            elif check == 1:
                await ctx.send('{0} was not found in the stream list'.format(arg))
        except:
            errormsg = str(traceback.print_exc())
            await errorchannel.send(errormsg)
            await ctx.send('An error occurred when removing {0}.'.format(arg))

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def query(ctx,arg):
    errorchannel = await client.fetch_channel(int(configdiscord["admin"]))

    if ctx.channel.name == "livestreams" or ctx.channel.name == "mods":
        try:
            check = querystream.main(arg)
            if check == 0:
                await ctx.send('{0} is in the stream list'.format(arg))
            elif check == 1:
                await ctx.send('{0} is not in the stream list.'.format(arg))
        except:
            errormsg = str(traceback.print_exc())
            await errorchannel.send(errormsg)
            await ctx.send('An error occurred when querying {0}.'.format(arg))

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def addgame(ctx,arg):
    errorchannel = await client.fetch_channel(int(configdiscord["admin"]))

    if ctx.channel.name == "mods":
        try:
            check = addsidegame.main(arg)
            if check == 0:
                await ctx.send('{0} has been added to the side games listing.'.format(arg))
            elif check == 1:
                await ctx.send('{0} already exists in the side games listing.'.format(arg))
            elif check == 2:
                await ctx.send('{0} does not seem to be an abbreviation. Please check the abbreviation of the game, then try again.'.format(arg))
            else:
                await ctx.send('Unknown error (Packle needs to check the logs')
        except:
            errormsg = str(traceback.print_exc())
            await errorchannel.send(errormsg)
            await ctx.send('An error occurred when querying {0}.'.format(arg))

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def removegame(ctx,arg):
    errorchannel = await client.fetch_channel(int(configdiscord["admin"]))

    if ctx.channel.name == "mods":
        try:
            check = removesidegame.main(arg)
            if check == 0:
                await ctx.send('{0} has been removed from the side games listing.'.format(arg))
            elif check == 1:
                await ctx.send('{0} was not found in the side games listing. Please make sure the abbreivation of the game is correct.'.format(arg))
        except:
            errormsg = str(traceback.print_exc())
            await errorchannel.send(errormsg)
            await ctx.send('An error occurred when removing {0}.'.format(arg))

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def querygames(ctx):
    errorchannel = await client.fetch_channel(int(configdiscord["admin"]))

    if ctx.channel.name == "mods":
        try:
            check = querysidegame.main()
            
            await ctx.send('The following games are in the side games listing: {0}'.format(check))
        except:
            errormsg = str(traceback.print_exc())
            await errorchannel.send(errormsg)
            await ctx.send('An error occurred when querying the game list.')

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        timeleft = round(error.retry_after)
        await ctx.send("This command is on cooldown, you can use it in {0} seconds".format(timeleft))

@tasks.loop(minutes=60)
async def change_status():
    errorchannel = await client.fetch_channel(int(configdiscord["admin"]))
    try:
        gamelist = configdiscord["statusmessage"]
        gamelist = gamelist.split(',')
        gamelistcount = len(gamelist) -1
        gamenum = random.randint(0,gamelistcount)
        gettime = time.localtime()
        gettime = time.strftime("%H:%M:%S", gettime)
        print("[{0}] [BOT] Changing game status to {1}".format(gettime,gamelist[gamenum].replace('"',"").replace("]","").replace("[","").strip()))
        await client.change_presence(activity=discord.Game(name=gamelist[gamenum].replace('"',"").replace("]","").replace("[","").strip()))
    except:
        errormsg = str(traceback.print_exc())
        await errorchannel.send(errormsg)

###########################################################################################################################################################################
###########################################################################################################################################################################
###########################################################################################################################################################################

@tasks.loop(minutes=5)
async def start_livestream():
    errorchannel = await client.fetch_channel(int(configdiscord["admin"]))
    configspeedrun = config["SpeedrunCom"]

    try:
        gettime = time.localtime()
        gettime = time.strftime("%H:%M:%S", gettime)
        print("[{0}] [TWITCH] Starting Twitch livestream checks...".format(gettime))

        streamchannel = client.get_channel(int(configdiscord["streamchannel"]))

        loadjson = open("./json/streamlist.json", "r")
        streamlist = json.load(loadjson)
        loadjson.close()

        checkjson = open("./json/online.json", "r")
        checkonlinelist = json.load(checkjson)
        checkjson.close()

        for key in streamlist["Streams"]["Twitch"]:
            username = key["username"]

            breaker = 0
            for onlinekey in checkonlinelist["Online"]:
                onlineuser = onlinekey["username"]
                if username.lower() == onlineuser.lower():
                    breaker = 1
                    print("--- {0} is online... Skipping...".format(username))
                    break

            if breaker == 0:
                online = livestream.execute(username)

                if isinstance(livestream,str):
                    await errorchannel.send(livestream)
                    pass
                if online == 0 or online == None:
                    pass
                else:
                    embed=discord.Embed(
                        title=online[2],
                        url="https://twitch.tv/"+online[0],
                        description="[Click here to watch](https://twitch.tv/{0})".format(online[0]),
                        color=random.randint(0, 0xFFFFFF),
                        timestamp=datetime.datetime.utcnow()
                    )
                    embed.set_author(name=online[0]+" is live on Twitch!", url="https://twitch.tv/"+online[0], icon_url=online[1])
                    embed.add_field(name="Game", value=online[3], inline=True)
                    embed.set_footer(text=configdiscord["botver"])
                    embed.set_image(url=online[4])
                    grabmessage = await streamchannel.send(embed=embed)

                    verify = await streamchannel.send("<@&{0}>".format(configspeedrun["Stream"]))

                    onlinejson = open("./json/online.json", "r")
                    onlinelist = json.load(onlinejson)
                    jsonupdate = {"username":online[0],"messageid":grabmessage.id,"alert":verify.id}
                    onlinelist["Online"].append(jsonupdate)
                    onlinejson.close()

                    onlinejson = open("./json/online.json","w")
                    onlinejson.write(json.dumps(onlinelist))
                    onlinejson.close()

        checkjson = open("./json/online.json", "r")
        checkonlinelist = json.load(checkjson)
        checkjson.close()

        for key in checkonlinelist["Online"]:
            username = key["username"]
            messageid = key["messageid"]
            alert = key["alert"]

            online = livestream.execute(username)
            if online == 0 or online == None:
                print("--- {0} has gone offline... Removing embed...".format(username))
                del key["username"]
                del key["messageid"]
                del key["alert"]

                messageid = int(messageid)
                verify = int(alert)

                finalid = await streamchannel.fetch_message(messageid)
                await finalid.delete()

                verifyid = await streamchannel.fetch_message(verify)
                await verifyid.delete()

                
            else:
                embed=discord.Embed(
                    title=online[2],
                    url="https://twitch.tv/"+online[0],
                    description="[Click here to watch](https://twitch.tv/{0})".format(online[0]),
                    color=random.randint(0, 0xFFFFFF),
                    timestamp=datetime.datetime.utcnow()
                )
                embed.set_author(name=online[0]+" is live on Twitch!", url="https://twitch.tv/"+online[0], icon_url=online[1])
                embed.add_field(name="Game", value=online[3], inline=True)
                embed.set_footer(text=configdiscord["botver"])
                embed.set_image(url=online[4])

                editid = await streamchannel.fetch_message(messageid)
                await editid.edit(embed=embed)

        onlinejson = open("./json/online.json", "w")

        checkonlinelist = json.dumps(checkonlinelist)
        checkonlinelist = checkonlinelist.replace('{}, ','').replace(', {}', '').replace('{}','').replace('\\','').replace('"{','').replace('}"','')

        onlinejson.write(checkonlinelist)
        onlinejson.close()
            
        
        gettime = time.localtime()
        gettime = time.strftime("%H:%M:%S", gettime)
        print("[{0}] [TWITCH] Completed Twitch livestream checks...".format(gettime))
    except:
        errormsg = str(traceback.print_exc())
        await errorchannel.send(errormsg)

@tasks.loop(minutes=20)
async def start_srcom():
    errorchannel = await client.fetch_channel(int(configdiscord["admin"]))

    gettime = time.localtime()
    gettime = time.strftime("%H:%M:%S", gettime)
    print("[{0}] [SRCOM] Checking Speedrun.com API for submissions...".format(gettime))
    submissionschannel = client.get_channel(int(configdiscord["subchannel"]))
    pbschannel = client.get_channel(int(configdiscord["pbchannel"]))
    configspeedrun = config["SpeedrunCom"]

    loadjson = open("./json/submissions.json", "r")
    submissions = json.load(loadjson)
    loadjson.close()

    games = requests.get("https://speedrun.com/api/v1/series/tonyhawk/games?max=50").json()["data"]

    for game in games:
        queue = requests.get("https://speedrun.com/api/v1/runs?status=new&game={0}".format(game["id"])).json()["data"]
        
        for lookup in queue:
            breaker = 0
            for submissionkey in submissions["Submitted"]:
                if submissionkey["id"] == lookup["id"]:
                    breaker = 1
                    break
            
            if breaker == 0:
                print("--- New submission found ({0})".format(lookup["id"]))
                unapprovedrun = srlookup.execute(lookup,0)
                
                if isinstance(unapprovedrun,str):
                    await errorchannel.send(unapprovedrun)
                    break

                if unapprovedrun["lvlid"] == "NoILFound" or unapprovedrun["subcatname"] == "(0)": 
                    title = unapprovedrun["gname"]
                else:
                    title = unapprovedrun["gname"] + " (IL)" 

                if unapprovedrun["subcatname"] == "(0)":
                    embed=discord.Embed(
                        title=title,
                        url=unapprovedrun["link"],
                        description="{0} in {1} {2}".format(unapprovedrun["cname"],unapprovedrun["time"],unapprovedrun["runtype"]),
                        color=random.randint(0, 0xFFFFFF),
                        timestamp=datetime.datetime.fromisoformat(unapprovedrun["date"][:-1])
                    )
                else:
                    embed=discord.Embed(
                        title=title,
                        url=unapprovedrun["link"],
                        description="{0} {1} in {2} {3}".format(unapprovedrun["cname"],unapprovedrun["subcatname"],unapprovedrun["time"],unapprovedrun["runtype"]),
                        color=random.randint(0, 0xFFFFFF),
                        timestamp=datetime.datetime.fromisoformat(unapprovedrun["date"][:-1])
                    )

                if unapprovedrun["pfp"] == None: embed.set_author(name=unapprovedrun["pname"], url=unapprovedrun["link"], icon_url="https://cdn.discordapp.com/attachments/83090266910621696/868581069492985946/3x.png")
                else: embed.set_author(name=unapprovedrun["pname"], url=unapprovedrun["link"], icon_url=unapprovedrun["pfp"])
                embed.set_footer(text=configdiscord["botver"])
                embed.set_thumbnail(url=unapprovedrun["gcover"])

                if ("IL" in title) and ("thps4" in unapprovedrun["abbr"]):
                    verify = await submissionschannel.send("<@&{0}>".format(configspeedrun["THPS4IL"]))
                else:
                    verify = await submissionschannel.send("<@&{0}>".format(configspeedrun[unapprovedrun["abbr"]]))
                grabmessage = await submissionschannel.send(embed=embed)

                onlinejson = open("./json/submissions.json", "r")
                onlinelist = json.load(onlinejson)

                jsonupdate = {"id":unapprovedrun["id"],"verifyid":verify.id,"messageid":grabmessage.id,"wrseconds":unapprovedrun["wrsecs"]}
                onlinelist["Submitted"].append(jsonupdate)
                onlinejson.close()

                onlinejson = open("./json/submissions.json","w")
                onlinejson.write(json.dumps(onlinelist))
                onlinejson.close()

    loadjson = open("./json/submissions.json", "r")
    submissions = json.load(loadjson)
    loadjson.close()

    for key in submissions["Submitted"]:
        runid = key["id"]
        messageid = key["messageid"]
        verifyid = key["verifyid"]

        print("--- Verifying status of {0}".format(runid))
        try:
            check = requests.get("https://speedrun.com/api/v1/runs/{0}".format(runid)).json()["data"]["status"]["status"]
        except:
            check = 0

        try:
            if check == "verified" or check == "rejected" or check == 0:
                if check == "verified":
                    print("--- {0} has been approved!".format(runid))
                    approval = srapproval.execute(runid)

                    if isinstance(approval,str):
                        await errorchannel.send(approval)
                        break
                    
                    if approval[0] > 0:
                        if approval[4]["lvlid"] != "NoILFound" and approval[4]["lvlid"] == None:
                            if approval[0] == 1:
                                discordtitle = "NEW IL WORLD RECORD!"
                            else:
                                discordtitle = "NEW IL PERSONAL BEST!"
                        else:
                            if approval[0] == 1:
                                discordtitle = "NEW WORLD RECORD!"
                            else:
                                discordtitle = "NEW PERSONAL BEST!"

                        if approval[0] == 1:
                            if approval[4]["subcatname"] == "(0)":
                                embed=discord.Embed(
                                    title="\U0001f3c6 {0} \U0001f3c6".format(discordtitle),
                                    url=approval[4]["link"],
                                    description="{0}\n{1} in {2} {3}".format(approval[4]["gname"],approval[4]["cname"],approval[4]["time"],approval[4]["runtype"]),
                                    color=random.randint(0, 0xFFFFFF),
                                    timestamp=datetime.datetime.fromisoformat(approval[6][:-1])
                                )
                            else:
                                embed=discord.Embed(
                                    title="\U0001f3c6 {0} \U0001f3c6".format(discordtitle),
                                    url=approval[4]["link"],
                                    description="{0}\n{1} {2} in {3} {4}".format(approval[4]["gname"],approval[4]["cname"],approval[4]["subcatname"],approval[4]["time"],approval[4]["runtype"]),
                                    color=random.randint(0, 0xFFFFFF),
                                    timestamp=datetime.datetime.fromisoformat(approval[6][:-1])
                                )

                        elif approval[0] == 2:
                            if approval[4]["subcatname"] == "(0)":
                                embed=discord.Embed(
                                    title="\U0001f948 {0} \U0001f948".format(discordtitle),
                                    url=approval[4]["link"],
                                    description="{0}\n{1} in {2} {3}".format(approval[4]["gname"],approval[4]["cname"],approval[4]["time"],approval[4]["runtype"]),
                                    color=random.randint(0, 0xFFFFFF),
                                    timestamp=datetime.datetime.fromisoformat(approval[6][:-1])
                                )
                            else:
                                embed=discord.Embed(
                                    title="\U0001f948 {0} \U0001f948".format(discordtitle),
                                    url=approval[4]["link"],
                                    description="{0}\n{1} {2} in {3} {4}".format(approval[4]["gname"],approval[4]["cname"],approval[4]["subcatname"],approval[4]["time"],approval[4]["runtype"]),
                                    color=random.randint(0, 0xFFFFFF),
                                    timestamp=datetime.datetime.fromisoformat(approval[6][:-1])
                                )

                        elif approval[0] == 3:
                            if approval[4]["subcatname"] == "(0)":
                                embed=discord.Embed(
                                    title="\U0001f949 {0} \U0001f949".format(discordtitle),
                                    url=approval[4]["link"],
                                    description="{0}\n{1} in {2} {3}".format(approval[4]["gname"],approval[4]["cname"],approval[4]["time"],approval[4]["runtype"]),
                                    color=random.randint(0, 0xFFFFFF),
                                    timestamp=datetime.datetime.fromisoformat(approval[6][:-1])
                                )
                            else:
                                embed=discord.Embed(
                                    title="\U0001f949 {0} \U0001f949".format(discordtitle),
                                    url=approval[4]["link"],
                                    description="{0}\n{1} {2} in {3} {4}".format(approval[4]["gname"],approval[4]["cname"],approval[4]["subcatname"],approval[4]["time"],approval[4]["runtype"]),
                                    color=random.randint(0, 0xFFFFFF),
                                    timestamp=datetime.datetime.fromisoformat(approval[6][:-1])
                                )

                        else:
                            if approval[4]["subcatname"] == "(0)":
                                embed=discord.Embed(
                                    title="{0}".format(discordtitle),
                                    url=approval[4]["link"],
                                    description="{0}\n{1} in {2} {3}".format(approval[4]["gname"],approval[4]["cname"],approval[4]["time"],approval[4]["runtype"]),
                                    color=random.randint(0, 0xFFFFFF),
                                    timestamp=datetime.datetime.fromisoformat(approval[6][:-1])
                                )
                            else:
                                embed=discord.Embed(
                                    title="{0}".format(discordtitle),
                                    url=approval[4]["link"],
                                    description="{0}\n{1} {2} in {3} {4}".format(approval[4]["gname"],approval[4]["cname"],approval[4]["subcatname"],approval[4]["time"],approval[4]["runtype"]),
                                    color=random.randint(0, 0xFFFFFF),
                                    timestamp=datetime.datetime.fromisoformat(approval[6][:-1])
                                )
                
                        if approval[4]["pfp"] == None: embed.set_author(name=approval[4]["pname"], url=approval[4]["link"], icon_url="https://cdn.discordapp.com/attachments/83090266910621696/868581069492985946/3x.png")
                        else: embed.set_author(name=approval[4]["pname"], url=approval[4]["link"], icon_url=approval[4]["pfp"])
                        embed.add_field(name="Placing", value="{0} / {1}".format(approval[0],approval[5]), inline=True)
                        embed.add_field(name="Points", value=approval[1], inline=True)
                        embed.add_field(name="Platform", value=approval[4]["platform"], inline=True)
                        
                        ctime = str(datetime.timedelta(seconds=approval[3]))
                        if key["wrseconds"] != "NoWR":
                            wtime = str(datetime.timedelta(seconds=key["wrseconds"]))

                            if float(approval[3]) > float(key["wrseconds"]):
                                delta = str(datetime.timedelta(seconds=(approval[3] - key["wrseconds"])))
                            else:
                                delta = str(datetime.timedelta(seconds=(key["wrseconds"]) - approval[3]))

                        if approval[4]["lvlid"] != "NoILFound":
                            if ("." in ctime) or ("." in delta):
                                ctime = ctime[:-3]
                                if key["wrseconds"] != "NoWR":
                                    wtime = wtime[:-3]
                                    delta = delta[:-3]
                        
                        if key["wrseconds"] == "NoWR":
                            embed.add_field(name="No Previous WR", value="No Previous WR", inline=True)
                        elif float(approval[3]) - float(key["wrseconds"]) == 0 and not approval[2] == approval[3]:
                            embed.add_field(name="Tied WR", value = "Tied WR", inline=True)
                        elif approval[0] == 1:
                            embed.add_field(name="Last WR [Delta]", value="{0} [-{1}]".format(wtime,delta), inline=True)
                        else:
                            embed.add_field(name="WR [Delta]", value="{0} [+{1}]".format(wtime,delta), inline=True)

                        embed.add_field(name="Completed Runs", value=approval[4]["ptotalruns"], inline=True)

                        if approval[4]["runcomment"] != None:
                            if len(approval[4]["runcomment"]) >= 500:
                                embed.add_field(name="Comments", value="*{0}...*".format(approval[4]["runcomment"][:450].replace("\r","")),inline=False)
                            else:
                                embed.add_field(name="Comments", value="*{0}*".format(approval[4]["runcomment"].replace("\r","")),inline=False)

                        embed.set_footer(text=configdiscord["botver"])
                        embed.set_thumbnail(url=approval[4]["gcover"])
                        await pbschannel.send(embed=embed)
                    else:
                        print("--- {0} is an obsolete submission.".format(runid))
                else:
                    print("--- {0} has been rejected or deleted...".format(runid))
                
                del key["id"]
                del key["verifyid"]
                del key["messageid"]
                del key["wrseconds"]

                messageid = int(messageid)

                finalid = await submissionschannel.fetch_message(messageid)
                await finalid.delete()

                time.sleep(1)

                finalid = await submissionschannel.fetch_message(verifyid)
                await finalid.delete()

                if approval[4]["pttv"] != 0:
                    loadjson = open("./json/streamlist.json", "r")
                    streamlist = json.load(loadjson)

                    streambreaker = 0
                    for key in streamlist["Streams"]["Twitch"]:
                        username = key["username"]
                        if username.casefold() == approval[4]["pttv"].casefold():
                            streambreaker = 1
                            break

                    if streambreaker == 0:
                        jsonupdate = {"username":approval[4]["pttv"].lower()}
                        streamlist["Streams"]["Twitch"].append(jsonupdate)

                        loadjson.close()
                        loadjson = open("./json/streamlist.json", "w")
                        loadjson.write(json.dumps(streamlist))
                        break
                    
                    loadjson.close()

        except Exception as exception:
            print(exception)

    onlinejson = open("./json/submissions.json", "w")

    submissions = json.dumps(submissions)
    submissions = submissions.replace('{}, ','').replace(', {}', '').replace('{}','').replace('\\','').replace('"{','').replace('}"','')

    onlinejson.write(submissions)
    onlinejson.close()

@tasks.loop(minutes=20)
async def start_side_srcom():
    errorchannel = await client.fetch_channel(int(configdiscord["admin"]))

    gettime = time.localtime()
    gettime = time.strftime("%H:%M:%S", gettime)
    print("[{0}] [SRCOM] Checking side game Speedrun.com API for submissions...".format(gettime))
    nonpbschannel = client.get_channel(int(configdiscord["nonpbchannel"]))

    loadjson = open("./json/sidesubmissions.json", "r")
    submissions = json.load(loadjson)
    loadjson.close()

    loadsidegamejson = open("./json/sidegames.json", "r")
    sidegames = json.load(loadsidegamejson)
    loadsidegamejson.close()

    for game in sidegames["Games"]:
        queue = requests.get("https://speedrun.com/api/v1/runs?status=new&game={0}".format(game["gameid"])).json()["data"]
        for lookup in queue:
            breaker = 0
            secondbreaker = 1
            for submissionkey in submissions["Submitted"]:
                if submissionkey["id"] == lookup["id"]:
                    breaker = 1
                    break
            
            runlookup = requests.get("https://speedrun.com/api/v1/users/{0}/personal-bests?embed=game".format(lookup["players"][0]["id"])).json()["data"]
            
            if breaker == 0:
                for run in runlookup:
                    gamename = run["game"]["data"]["names"]["international"]

                    if "Tony Hawk" in gamename or "THPS" in gamename:
                        secondbreaker = 0
                        break

            if secondbreaker == 1:
                print("--- Skipping out on current run...")
            elif secondbreaker == 0:
                print("--- New submission found ({0})".format(lookup["id"]))
                unapprovedrun = srlookup.execute(lookup,0)
                
                if isinstance(unapprovedrun,str):
                    await errorchannel.send(unapprovedrun)
                    break

                onlinejson = open("./json/sidesubmissions.json", "r")
                onlinelist = json.load(onlinejson)
                jsonupdate = {"id":unapprovedrun["id"],"wrseconds":unapprovedrun["wrsecs"]}
                onlinelist["Submitted"].append(jsonupdate)
                onlinejson.close()

                onlinejson = open("./json/sidesubmissions.json","w")
                onlinejson.write(json.dumps(onlinelist))
                onlinejson.close()

    loadjson = open("./json/sidesubmissions.json", "r")
    submissions = json.load(loadjson)
    loadjson.close()

    for key in submissions["Submitted"]:
        runid = key["id"]

        print("--- Verifying status of {0}".format(runid))
        try:
            check = requests.get("https://speedrun.com/api/v1/runs/{0}".format(runid)).json()["data"]["status"]["status"]
        except:
            check = 0

        try:
            if check == "verified" or check == "rejected" or check == 0:
                if check == "verified":
                    print("--- {0} has been approved!".format(runid))
                    approval = srapproval.execute(runid)

                    if isinstance(approval,str):
                        await errorchannel.send(approval)
                        break
                    
                    if approval[0] == 1:
                        if approval[4]["subcatname"] == "(0)":
                            embed=discord.Embed(
                                title="NEW VERIFIED TIME FOR {0}".format(approval[4]["gname"].upper()),
                                url=approval[4]["link"],
                                description="{0}\n{1} in {2} {3}".format(approval[4]["gname"],approval[4]["cname"],approval[4]["time"],approval[4]["runtype"]),
                                color=random.randint(0, 0xFFFFFF),
                                timestamp=datetime.datetime.fromisoformat(approval[6][:-1])
                            )
                
                        if approval[4]["pfp"] == None: embed.set_author(name=approval[4]["pname"], url=approval[4]["link"], icon_url="https://cdn.discordapp.com/attachments/83090266910621696/868581069492985946/3x.png")
                        else: embed.set_author(name=approval[4]["pname"], url=approval[4]["link"], icon_url=approval[4]["pfp"])
                        embed.add_field(name="Placing", value="{0} / {1}".format(approval[0],approval[5]), inline=True)
                        embed.add_field(name="Platform", value=approval[4]["platform"], inline=True)
                        
                        ctime = str(datetime.timedelta(seconds=approval[3]))
                        if key["wrseconds"] != "NoWR":
                            wtime = str(datetime.timedelta(seconds=key["wrseconds"]))

                            if float(approval[3]) > float(key["wrseconds"]):
                                delta = str(datetime.timedelta(seconds=(approval[3] - key["wrseconds"])))
                            else:
                                delta = str(datetime.timedelta(seconds=(key["wrseconds"]) - approval[3]))

                        if approval[4]["lvlid"] != "NoILFound":
                            if "." in ctime:
                                ctime = ctime[:-3]
                                if key["wrseconds"] != "NoWR":
                                    wtime = wtime[:-3]
                                    delta = delta[:-3]
                        
                        if key["wrseconds"] == "NoWR":
                            embed.add_field(name="No Previous WR", value="No Previous WR", inline=True)
                        elif float(approval[3]) == float(key["wrseconds"]):
                            embed.add_field(name="Tied WR", value = "Tied WR", inline=True)
                        elif approval[0] == 1:
                            embed.add_field(name="Last WR [Delta]", value="{0} [-{1}]".format(wtime,delta), inline=True)
                        else:
                            embed.add_field(name="WR [Delta]", value="{0} [+{1}]".format(ctime,delta), inline=True)

                        embed.add_field(name="Completed Runs", value=approval[4]["ptotalruns"], inline=True)

                        if approval[4]["runcomment"] != None:
                            if len(approval[4]["runcomment"]) >= 500:
                                embed.add_field(name="Comments", value="*{0}...*".format(approval[4]["runcomment"][:450].replace("\r","")),inline=False)
                            else:
                                embed.add_field(name="Comments", value="*{0}*".format(approval[4]["runcomment"].replace("\r","")),inline=False)

                        embed.set_footer(text=configdiscord["botver"])
                        embed.set_thumbnail(url=approval[4]["gcover"])
                        await nonpbschannel.send(embed=embed)
                    else:
                        print("--- {0} is an obsolete submission.".format(runid))
                else:
                    print("--- {0} has been rejected or deleted...".format(runid))

                del key["id"]
                del key["wrseconds"]

        except Exception as exception:
            print(exception)

    onlinejson = open("./json/sidesubmissions.json", "w")

    submissions = json.dumps(submissions)
    submissions = submissions.replace('{}, ','').replace(', {}', '').replace('{}','').replace('\\','').replace('"{','').replace('}"','')

    onlinejson.write(submissions)
    onlinejson.close()


client.run(configdiscord["distoken"])