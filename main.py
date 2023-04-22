###########################################################################################################################################################################
# THPSBot v2.0.1
# BY THEPACKLE (https://twitter.com/thepackle)
###########################################################################################################################################################################
import os,requests,sys,discord,random,datetime,time,traceback,glob,sqlite3
from commands import sidegame_add,sidegame_query,sidegame_remove
from commands import ttv_add,ttv_query,ttv_remove
from commands import status_add,status_query,status_remove
from functions import rungg_lookup,ttv_lookup
from functions import src_approval,src_lookup,src_api_call
from functions import local_streamdb,local_onlinedb,local_submissionsdb,local_sidegamesdb,local_tonysdb
from dbs import config
from discord import File
from io import BytesIO
from urllib.parse import urlparse
from discord.ext import tasks,commands
from PIL import Image
###########################################################################################################################################################################
###########################################################################################################################################################################

intents = discord.Intents.all()
client  = commands.Bot(intents=intents)
debug   = 0 # 0 = PROD; 1 = DEBUG

while True and debug == 0:
    current_time = time.localtime()
    if current_time.tm_min == 0 or current_time.tm_min == 30:
        break
    minutes_until_start = 30 - current_time.tm_min % 30
    print(f"{minutes_until_start} minute(s) until script starts")
    time.sleep(30)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    await change_status()

    global errorchannel
    errorchannel = await client.fetch_channel(int(config.channels["error"]))

    if not start_livestream.is_running():
        start_livestream.start()

    if not change_status.is_running():
        change_status.start()

    if not change_pfp.is_running():
        change_pfp.start()

    if not start_srcom.is_running():
        start_srcom.start()

    if not start_side_srcom.is_running():
        start_side_srcom.start()

@client.slash_command(description="Quick check to see if the bot is responding to requests.")
@commands.cooldown(1, 10, commands.BucketType.user)
async def ping(ctx):
    await ctx.respond(f"Hello, {ctx.author}! If you are seeing this, I am online. If something is broken, blame Packle.", ephemeral=True)

@client.slash_command(name="status",description="Add a new status message that the bot can cycle through.")
async def status(
    ctx: discord.ApplicationContext,
    status: discord.Option(str, choices=["Add","Remove","Query"]),
    message: discord.Option(str)
):
    try:
        if status == "Add":
            check = await status_add.main(message)
            if check == 0:
                await ctx.respond(f"'{message}' was added to the status list.")
            elif check == 1:
                await ctx.respond(f"'{message}' waas already in the stream list.")
        
        elif status == "Remove":
            check = await status_remove.main(message)
            if check == 0:
                await ctx.respond(f"{message} was removed to the status list.")
            elif check == 1:
                await ctx.respond(f"{message} was not found in the status list")

        elif status == "Query":
            check = await status_query.main(message)
            if check == 0:
                await ctx.respond(f"{message} is in the status list.")
            elif check == 1:
                await ctx.respond(f"{message} is not in the status list.")
    except:
        await errorchannel.send("[ADDING] Status message error")
        await ctx.send(f"An error occurred when adding '{message}'.")

@client.slash_command(name="stream",description="Add or remove users from the livestream list or query it!")
async def stream(
    ctx: discord.ApplicationContext,
    option: discord.Option(str, choices=["Add","Remove","Query"]),
    user: discord.Option(str)
):
    try:
        if option == "Add":
            check = await ttv_add.main(user)
            if check == 0:
                await ctx.respond(f"{user} was added to the stream list.")
            elif check == 1:
                await ctx.respond(f"{user} was already in the stream list.")

        elif option == "Remove":
            check = await ttv_remove.main(user)
            if check == 0:
                await ctx.respond(f"{user} was removed to the stream list.")
            elif check == 1:
                await ctx.respond(f"{user} was not found in the stream list")

        elif option == "Query":
            check = await ttv_query.main(user)
            if check == 0:
                await ctx.respond(f"{user} is in the stream list.")
            elif check == 1:
                await ctx.respond(f"{user} is not in the stream list.")
    except:
        await errorchannel.send("[QUERY] Twitch stream list error")
        await ctx.send(f"An error occurred when dealing with a new stream list. {user}.")

@client.slash_command(name="sidegames",description="Add or remove users from the side games listor query it!")
async def stream(
    ctx: discord.ApplicationContext,
    option: discord.Option(str, choices=["Add","Remove","Query"]),
    game: discord.Option(str)
):
    try:
        if option == "Add":
            check = await sidegame_add.main(game)
            if check == 0:
                await ctx.respond(f"{game} has been added to the side games listing.")
            elif check == 1:
                await ctx.respond(f"{game} already exists in the side games listing.")
            else:
                await ctx.respond(f"{game} does not seem to be an abbreviation. Please check the abbreviation of the game, then try again.")
        elif option == "Remove":
            check = await sidegame_remove.main(game)
            if check == 0:
                await ctx.respond(f"{game} has been removed from the side games listing.")
            elif check == 1:
                await ctx.respond(f"{game} was not found in the side games listing. Please make sure the abbreivation of the game is correct.")
        elif option == "Query":
            check = await sidegame_query.main(game)
            if check == 0:
                await ctx.respond(f"{game} is in the side games listing.")
            elif check == 1:
                await ctx.respond(f"{game} either does not exist or is not an abbreviation.")
    except:
        await errorchannel.send("[QUERY] Side games list error")
        await ctx.send("An error occurred with the game list.")

pfp = discord.SlashCommandGroup("pfp", "Set a profile picture to THPSBot or add a new one!")
async def get_pfp_filenames(ctx: discord.AutocompleteContext):
    pfps = os.listdir("pfp")
    return pfps
    
@pfp.command()
async def add(ctx, url: str):
    try:
        url_parts = urlparse(url)
        fileextension = os.path.splitext(url_parts.path)[1]

        if fileextension.lower() == ".jpg" or fileextension.lower() == ".png":
            response = requests.get(url)
            response.raise_for_status()

            resp = Image.open(BytesIO(response.content))
            image = resp.resize((128,128))

            author = ctx.author
            await ctx.respond(f"{author.mention}, what is the new name of the file? (30 second timeout)")
            new_file = await client.wait_for("message", check=lambda m: m.author.id == author.id and m.channel.id == ctx.channel.id, timeout=30.0)
            new_filename = new_file.content
            await new_file.delete()

            with open(f"pfp/{new_filename}{fileextension}", "wb") as u:
                image.save(u,fileextension.strip("."))
            
            await ctx.respond(f"{new_filename} has been successfully added!")
        else:
            await ctx.respond(f"The URL provided is not a .jpg or .png file.")
    except requests.exceptions.HTTPError as error:
        await ctx.respond(f"An HTTPError exception was raised: {error}")
    except TimeoutError as error:
        await ctx.respond(f"Request timed out: {error}")
    except Exception as error:
        await ctx.respond(f"An error occurred: {error}").defer()

@pfp.command()
async def set(ctx, pic: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(get_pfp_filenames))):
    try:
        with open(os.path.join("pfp", pic), "rb") as f:
            avatar = f.read()
        await client.user.edit(avatar=avatar)
        await ctx.respond(f"Forced the new profile picture as {pic}")
    except:
        await ctx.respond("An error occurred when trying to force a profile picture.")

client.add_application_command(pfp)

@client.slash_command(description="Restart the bot. (Requires admin)")
@commands.has_role(config.adminroles["admin"])
async def restart(ctx):
    try:
        await ctx.respond("Restarting THPSBot...")
        os.execv(sys.executable, ['python'] + sys.argv)
    except:
        await ctx.respond("")

@client.slash_command(description="Create a new poll with reactions already added!")
async def poll(ctx, *, question):
    try:
        await ctx.respond("Creating poll...", ephemeral=True)
        poll_msg = await ctx.send(question)

        await poll_msg.add_reaction("✅")
        await poll_msg.add_reaction("❌")
    except:
        await ctx.respond("An error occurred when trying to make a poll.")

###########################################################################################################################################################################
###########################################################################################################################################################################
@client.event
async def on_raw_reaction_add(message):
    try:
        if message.emoji.id == config.tonysemoji and message.channel_id in config.tonyschannels:
            channelid = message.channel_id
            channel   = client.get_channel(channelid)
            message   = await channel.fetch_message(message.message_id)

            existing_reactions = [
                reaction.emoji.id for reaction in message.reactions
                if reaction.emoji.id == config.tonysemoji
            ]
            if len(existing_reactions) > 1:
                await message.remove_reaction(config.tonysemoji,message.author)
            else:
                await local_tonysdb.main(0,(message.id,message.author.display_name,message.channel.name,message.content,message.created_at))
    except:
        await errorchannel.send("An error occurred when checking the reactions for the Tony's.")

@client.event
async def on_raw_reaction_remove(message):
    try:
        if message.emoji.id == config.tonysemoji and message.channel_id in config.tonyschannels:
            channelid = message.channel_id
            channel   = client.get_channel(channelid)
            message   = await channel.fetch_message(message.message_id)

            existing_reactions = [
                reaction.emoji.id for reaction in message.reactions
                if reaction.emoji.id == config.tonysemoji
            ]
            if len(existing_reactions) < 1:
                await local_tonysdb.main(1,message.id)
    except:
        await errorchannel.send("An error occurred when checking the reactions for the Tony's.")

@client.event
async def on_command_error(message, error):
    if isinstance(error, commands.CommandOnCooldown):
        timeleft = round(error.retry_after)
        await message.send(f"This command is on cooldown, you can use it in {timeleft} seconds")

@tasks.loop(minutes=60)
async def change_status():
    try:
        connect = sqlite3.connect("dbs/statusmsg.db")
        cursor  = connect.cursor()
        cursor.execute("SELECT text FROM games ORDER BY RANDOM() LIMIT 1")
        game = cursor.fetchone()
        connect.close()

        print(f"[{time.strftime('%H:%M:%S', time.localtime())}] [BOT] Changing game status to {game[0]}")
        await client.change_presence(activity=discord.Game(name=game[0]))
    except:
        await errorchannel.send("[STATUS] Status update error")

@tasks.loop(hours=24)
async def change_pfp():
    errorchannel = await client.fetch_channel(int(config.channels["error"]))
    try:
        pfp_list  = glob.glob("pfp/*")
        pfp_count = len(pfp_list) -1
        pfp_num   = random.randint(0,pfp_count)
        with open(pfp_list[pfp_num], 'rb') as image:
            await client.user.edit(avatar=image.read())
    except:
        await errorchannel.send("[PFP] PFP update error")

###########################################################################################################################################################################
###########################################################################################################################################################################

@tasks.loop(minutes=1)
async def start_livestream():
    try:
        print(f"[{time.strftime('%H:%M:%S', time.localtime())}] [TWITCH] Starting Twitch livestream checks...")

        streamchannel   = client.get_channel(int(config.channels["stream"]))

        streamlist      = await local_streamdb.main(0,0)
        onlinelist      = await local_onlinedb.main(0,0)
        #youtubelist    = await local_onlinedb.main(3,0)
        twitchlist      = await ttv_lookup.main(streamlist)
        fulltwitchlist  = [row["user"].casefold() for row in twitchlist]
        fullonlinelist  = [row[0].casefold() for row in onlinelist]

        if isinstance(twitchlist,str):
            await errorchannel.send(twitchlist)
        else:
            if len(twitchlist) > 0:
                for stream in twitchlist:
                    rungg = await rungg_lookup.main(stream["user"])

                    if stream["user"].casefold() in fullonlinelist:
                        for index, data in enumerate(onlinelist):
                            if data[0].casefold() == stream["user"].casefold():
                                onlineindex = index

                        print(f"--- {stream['user']} is online, updating embed.")
                        messageid = int(onlinelist[onlineindex][1])

                        embed=discord.Embed(
                            title=stream["title"],
                            url="https://twitch.tv/"+stream["user"],
                            description=f"[Click here to watch](https://twitch.tv/{stream['user']})",
                            color=random.randint(0, 0xFFFFFF),
                            timestamp=datetime.datetime.utcnow()
                        )
                        
                        embed.set_author(name=stream["user"]+" is live on Twitch!", url="https://twitch.tv/"+stream["user"], icon_url=stream["pfp"])
                        embed.add_field(name="Game", value=stream["gname"], inline=True)
                        embed.set_footer(text=config.botver)
                        embed.set_image(url=stream["tnail"])
                        
                        if len(rungg) > 0:
                            rungg = rungg[0]
                            embed.add_field(name="Category", value=rungg["category"], inline=True)
                            embed.add_field(name="", value="", inline=False)

                            if rungg["hasReset"] == False:
                                if rungg["lastSplitName"] != False:
                                    embed.add_field(name="Previous Split [Delta]", value=f"{rungg['lastSplitName']} [{rungg['lastSplitTime']}]", inline=True)
                                
                                embed.add_field(name="Current Split", value=rungg["currentSplit"], inline=True)
                            else:
                                embed.add_field(name="Status", value="Run Reset", inline=True)

                        editid = await streamchannel.fetch_message(messageid)
                        await editid.edit(embed=embed)

                    elif stream["user"] != "NA":
                        embed=discord.Embed(
                            title=stream["title"],
                            url="https://twitch.tv/"+stream["user"],
                            description=f"[Click here to watch](https://twitch.tv/{stream['user']})",
                            color=random.randint(0, 0xFFFFFF),
                            timestamp=datetime.datetime.utcnow()
                        )

                        embed.set_author(name=stream["user"]+" is live on Twitch!", url="https://twitch.tv/"+stream["user"], icon_url=stream["pfp"])
                        embed.set_footer(text=config.botver)
                        embed.set_image(url=stream["tnail"])
                        embed.add_field(name="Game", value=stream["gname"], inline=True)

                        if len(rungg) > 0:
                            rungg = rungg[0]                   
                            embed.add_field(name="Category", value=rungg["category"], inline=True)
                            embed.add_field(name="", value="", inline=False)

                            if rungg["hasReset"] == False:
                                if rungg["lastSplitName"] != False:
                                    embed.add_field(name="Previous Split [Delta]", value=f"{rungg['lastSplitName']} [{rungg['lastSplitTime']}]", inline=True)
                                
                                embed.add_field(name="Current Split", value=rungg["currentSplit"], inline=True)
                            else:
                                embed.add_field(name="Status", value="Run Reset", inline=True)

                        grabmessage = await streamchannel.send(embed=embed)
                        verify = await streamchannel.send(f"<@&{config.roles['Stream']}>")

                        await local_onlinedb.main(1,(stream["user"].casefold(),grabmessage.id,verify.id))

            for onlinecheck in onlinelist:
                if onlinecheck[0].casefold() not in fulltwitchlist and onlinecheck != "NA":
                    print(f"--- {onlinecheck[0].casefold()} is now offline.")

                    finalid = await streamchannel.fetch_message(int(onlinecheck[1]))
                    verifyid = await streamchannel.fetch_message(int(onlinecheck[2]))

                    await finalid.delete()
                    await verifyid.delete()
                    onlinelist = await local_onlinedb.main(2,onlinecheck[0].casefold())
        
        print(f"[{time.strftime('%H:%M:%S', time.localtime())}] [TWITCH] Completed Twitch livestream checks...")

    except:
        print(traceback.format_exc())
        await errorchannel.send("[LIVESTREAM STATUS] An unknown error occurred")

@tasks.loop(minutes=30)
async def start_srcom():
    try:
        submissionschannel = client.get_channel(int(config.channels["sub"]))
        pbschannel = client.get_channel(int(config.channels["pb"]))

        print(f"[{time.strftime('%H:%M:%S', time.localtime())}] [SRCOM] Checking Speedrun.com API for submissions...")

        games = await src_api_call.main("https://speedrun.com/api/v1/series/tonyhawk/games?max=50")

        for game in games:
            queue = await src_api_call.main(f"https://speedrun.com/api/v1/runs?status=new&game={game['id']}")
            
            for lookup in queue:
                breaker = 0

                submissions = await local_submissionsdb.main(0,0)
                for submission in submissions:
                    if submission[0] == lookup["id"]:
                        breaker = 1
                        break
                
                if breaker == 0:
                    print(f"--- New submission found ({lookup['id']})")
                    unapprovedrun = await src_lookup.main(0,lookup)
                    
                    if isinstance(unapprovedrun,str):
                        await errorchannel.send(unapprovedrun)
                        break

                    if unapprovedrun["lvlid"] == "NoILFound" or unapprovedrun["subcatname"] == "(0)": title = unapprovedrun["gname"]
                    else: title = unapprovedrun["gname"] + " (IL)" 

                    embed = discord.Embed(
                        title=title,
                        url=unapprovedrun["link"],
                        color=random.randint(0, 0xFFFFFF),
                        timestamp=datetime.datetime.fromisoformat(unapprovedrun["date"][:-1])
                    )
                    embed = embed.to_dict()

                    if unapprovedrun["subcatname"] == "(0)":
                        embed.update({"description": f"{unapprovedrun['cname']} in {unapprovedrun['time']} {unapprovedrun['runtype']}"})
                    else:
                        embed.update({"description": f"{unapprovedrun['cname']} {unapprovedrun['subcatname']} in {unapprovedrun['time']} {unapprovedrun['runtype']}"})

                    embed = discord.Embed.from_dict(embed)

                    if unapprovedrun["pfp"] == None: embed.set_author(name=unapprovedrun["pname"], url=unapprovedrun["link"], icon_url="https://cdn.discordapp.com/attachments/83090266910621696/868581069492985946/3x.png")
                    else: embed.set_author(name=unapprovedrun["pname"], url=unapprovedrun["link"], icon_url=unapprovedrun["pfp"])
                    embed.set_footer(text=config.botver)
                    embed.set_thumbnail(url=unapprovedrun["gcover"])

                    try:
                        if ("IL" in title) and ("thps4" in unapprovedrun["abbr"]) and ("thps4ce" not in unapprovedrun["abbr"]):
                            verify = await submissionschannel.send("<@&{0}>".format(config.roles["THPS4IL"]))
                        elif ("gbc" in unapprovedrun["abbr"]):
                            verify = await submissionschannel.send("<@&{0}>".format(config.roles[unapprovedrun["abbr"]].upper()).replace("gbc",""))
                        elif ("gba" in unapprovedrun["abbr"]):
                            verify = await submissionschannel.send("<@&{0}>".format(config.roles[unapprovedrun["abbr"]].upper()).replace("gba",""))
                        elif ("psp" in unapprovedrun["abbr"]) :
                            verify = await submissionschannel.send("<@&{0}>".format(config.roles[unapprovedrun["abbr"]].upper()).replace("psp",""))
                        else:
                            verify = await submissionschannel.send("<@&{0}>".format(config.roles[unapprovedrun["abbr"].upper()]))
                    except:
                        verify = await submissionschannel.send("No role found")

                    grabmessage = await submissionschannel.send(embed=embed)

                    subtuple = (unapprovedrun["id"],verify.id,grabmessage.id,unapprovedrun["wrsecs"])
                    await local_submissionsdb.main(1,subtuple)

        submissions = await local_submissionsdb.main(0,0)

        for submission in submissions:
            runid = submission[0]
            verifyid = submission[1]
            messageid = submission[2]
            
            print(f"--- Verifying status of {runid}")
            check = await src_api_call.main(f"https://speedrun.com/api/v1/runs/{runid}")
            check = check["status"]["status"]
            if isinstance(check, int):
                print("--- AN ERROR OCCURRED!")
                return

            if check == "verified" or check == "rejected" or check == 0:
                if check == "verified":
                    print(f"--- {runid} has been approved!")
                    approval = await src_approval.main(runid)

                    if isinstance(approval,str):
                        await errorchannel.send(approval)
                        break
                    
                    if approval[0] > 0:
                        if approval[4]["lvlid"] != "NoILFound" and approval[4]["lvlid"] == None:
                            if approval[0] == 1: discordtitle = "NEW IL WORLD RECORD!"
                            else: discordtitle = "NEW IL PERSONAL BEST!"
                        else:
                            if approval[0] == 1: discordtitle = "NEW WORLD RECORD!"
                            else: discordtitle = "NEW PERSONAL BEST!"

                        embed = discord.Embed(
                                url=approval[4]["link"],
                                color=random.randint(0, 0xFFFFFF),
                                timestamp=datetime.datetime.fromisoformat(approval[6][:-1])
                            )
                        embed = embed.to_dict()

                        if approval[0] == 1:
                            if approval[4]["subcatname"] == "(0)":
                                embed.update({"title": f"\U0001f3c6 {discordtitle} \U0001f3c6"})
                                embed.update({"description": f"{approval[4]['gname']}\n{approval[4]['cname']} in {approval[4]['time']} {approval[4]['runtype']}"})
                            else:
                                embed.update({"title": f"\U0001f3c6 {discordtitle} \U0001f3c6"})
                                embed.update({"description": f"{approval[4]['gname']}\n{approval[4]['cname']} {approval[4]['subcatname']} in {approval[4]['time']} {approval[4]['runtype']}"})

                        elif approval[0] == 2:
                            if approval[4]["subcatname"] == "(0)":
                                embed.update({"title": f"\U0001f948 {discordtitle} \U0001f948"})
                                embed.update({"description": f"{approval[4]['gname']}\n{approval[4]['cname']} in {approval[4]['time']} {approval[4]['runtype']}"})
                            else:
                                embed.update({"title": f"\U0001f948 {discordtitle} \U0001f948"})
                                embed.update({"description": f"{approval[4]['gname']}\n{approval[4]['cname']} {approval[4]['subcatname']} in {approval[4]['time']} {approval[4]['runtype']}"})

                        elif approval[0] == 3:
                            if approval[4]["subcatname"] == "(0)":
                                embed.update({"title": f"\U0001f949 {discordtitle} \U0001f949"})
                                embed.update({"description": f"{approval[4]['gname']}\n{approval[4]['cname']} in {approval[4]['time']} {approval[4]['runtype']}"})
                            else:
                                embed.update({"title": f"\U0001f949 {discordtitle} \U0001f949"})
                                embed.update({"description": f"{approval[4]['gname']}\n{approval[4]['cname']} {approval[4]['subcatname']} in {approval[4]['time']} {approval[4]['runtype']}"})

                        else:
                            if approval[4]["subcatname"] == "(0)":
                                embed.update({"title": f"{discordtitle}"})
                                embed.update({"description": f"{approval[4]['gname']}\n{approval[4]['cname']} in {approval[4]['time']} {approval[4]['runtype']}"})
                            else:
                                embed.update({"title": f"{discordtitle}"})
                                embed.update({"description": f"{approval[4]['gname']}\n{approval[4]['cname']} {approval[4]['subcatname']} in {approval[4]['time']} {approval[4]['runtype']}"})
                
                        embed = discord.Embed.from_dict(embed)

                        if approval[4]["pfp"] == None: embed.set_author(name=approval[4]["pname"], url=f"https://speedrun.com/{approval[4]['pname']}", icon_url="https://cdn.discordapp.com/attachments/83090266910621696/868581069492985946/3x.png")
                        else: embed.set_author(name=approval[4]["pname"], url=f"https://speedrun.com/{approval[4]['pname']}", icon_url=approval[4]["pfp"])
                        embed.add_field(name="Placing", value=f"{approval[0]} / {approval[5]}", inline=True)
                        embed.add_field(name="Points", value=approval[1], inline=True)
                        embed.add_field(name="Platform", value=approval[4]["platform"], inline=True)
                        
                        ctime = str(datetime.timedelta(seconds=approval[3]))
                        if submission[3] != "NoWR":
                            wtime = str(datetime.timedelta(seconds=submission[3]))

                            if float(approval[3]) > float(submission[3]):
                                delta = str(datetime.timedelta(seconds=(approval[3] - submission[3])))
                            else:
                                delta = str(datetime.timedelta(seconds=(submission[3]) - approval[3]))

                        if approval[4]["lvlid"] != "NoILFound":
                            if "." in ctime:
                                ctime = ctime[:-3]
                                if submission[3] != "NoWR":
                                    wtime = wtime[:-3]
                                    delta = delta[:-3]
                        
                        if submission[3] == "NoWR":
                            embed.add_field(name="No Previous WR", value="No Previous WR", inline=True)
                        elif float(approval[3]) - float(submission[3]) == 0 and not approval[2] == approval[3]:
                            embed.add_field(name="Tied WR", value = "Tied WR", inline=True)
                        elif approval[0] == 1:
                            embed.add_field(name="Last WR [Delta]", value=f"{wtime} [-{delta}]", inline=True)
                        else:
                            embed.add_field(name="WR [Delta]", value=f"{wtime} [+{delta}]", inline=True)

                        embed.add_field(name="Completed Runs", value=approval[4]["ptotalruns"], inline=True)

                        if approval[4]["runcomment"] != None:
                            if len(approval[4]["runcomment"]) >= 350:
                                embed.add_field(name="Comments", value="*`{0}...*`".format(approval[4]["runcomment"][:300].replace("\r","")),inline=False)
                            else:
                                embed.add_field(name="Comments", value="*{0}*".format(approval[4]["runcomment"].replace("\r","")),inline=False)

                        embed.set_footer(text=config.botver)
                        embed.set_thumbnail(url=approval[4]["gcover"])

                        await pbschannel.send(embed=embed)
                    else:
                        print(f"--- {runid} is an obsolete submission.")
                else:
                    print(f"--- {runid} has been rejected or deleted...")
                
                await local_submissionsdb.main(2,runid)

                messageid = int(messageid)

                finalid = await submissionschannel.fetch_message(messageid)
                await finalid.delete()

                time.sleep(.500)

                finalid = await submissionschannel.fetch_message(verifyid)
                await finalid.delete()

                if approval[4]["pttv"] != 0:
                    onlinelist = await local_streamdb.main(0,0)
                    if approval[4]["pttv"].casefold() not in onlinelist:
                        await local_streamdb.main(1,approval[4]["pttv"].lower())

    except Exception as exception:
        print(exception)

@tasks.loop(minutes=30)
async def start_side_srcom():
    try:
        print(f"[{time.strftime('%H:%M:%S', time.localtime())}] [SRCOM] Checking side game Speedrun.com API for submissions...")
        nonpbschannel = client.get_channel(int(config.channels["nonpb"]))

        sidegames = await local_sidegamesdb.main()
        submissions = await local_submissionsdb.main(3,0)

        for game in [row.casefold() for row in sidegames]:
            queue = await src_api_call.main(f"https://speedrun.com/api/v1/runs?status=new&game={game}")

            for lookup in queue:
                if lookup["id"] in [row[0].casefold() for row in submissions]:
                    break

                runlookup = await src_api_call.main(f"https://speedrun.com/api/v1/users/{lookup['players'][0]['id']}/personal-bests?embed=game")
                            
                for run in runlookup:
                    gamename = run["game"]["data"]["names"]["international"]
                    if "Tony Hawk" in gamename or "THPS" in gamename:
                        break

                print(f"--- New submission found ({lookup['id']})")
                unapprovedrun = await src_lookup.main(0,lookup)
                
                if isinstance(unapprovedrun,str):
                    await errorchannel.send("Error encountered running start_side_srcom")
                    break

                await local_submissionsdb.main(4,{"id":unapprovedrun["id"],"wrseconds":unapprovedrun["wrsecs"]})

        for key in submissions:
            print(f"--- Verifying status of {key[0]}")
            check = await src_api_call.main(f"https://speedrun.com/api/v1/runs/{key[0]}")["status"]["status"]
            
            if check == "verified" or check == "rejected" or check == 0:
                if check == "verified":
                    print(f"--- {key[0]} has been approved!")
                    approval = await src_approval.main(key[0])

                    if isinstance(approval,str):
                        await errorchannel.send(approval)
                        break
                    
                    if approval[0] == 1:
                        embed = discord.Embed(
                            title="NEW VERIFIED TIME",
                            url=approval[4]["link"],
                            description=f"{approval[4]['gname']}\n{approval[4]['cname']} in {approval[4]['time']} {approval[4]['runtype']}",
                            color=random.randint(0, 0xFFFFFF),
                            timestamp=datetime.datetime.fromisoformat(approval[6][:-1])
                        )
                
                        if approval[4]["pfp"] == None: embed.set_author(name=approval[4]["pname"], url=approval[4]["link"], icon_url="https://cdn.discordapp.com/attachments/83090266910621696/868581069492985946/3x.png")
                        else: embed.set_author(name=approval[4]["pname"], url=approval[4]["link"], icon_url=approval[4]["pfp"])
                        embed.add_field(name="Placing", value=f"{approval[0]} / {approval[5]}", inline=True)
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
                            embed.add_field(name="Last WR [Delta]", value=f"{wtime} [-{delta}]", inline=True)
                        else:
                            embed.add_field(name="WR [Delta]", value=f"{ctime} [+{delta}]", inline=True)

                        embed.add_field(name="Completed Runs", value=approval[4]["ptotalruns"], inline=True)

                        if approval[4]["runcomment"] != None:
                            if len(approval[4]["runcomment"]) >= 350:
                                    embed.add_field(name="Comments", value="*`{0}...*`".format(approval[4]["runcomment"][:300].replace("\r","")),inline=False)
                            else:
                                embed.add_field(name="Comments", value="*{0}*".format(approval[4]["runcomment"].replace("\r","")),inline=False)

                        embed.set_footer(text=config.botver) 
                        embed.set_thumbnail(url=approval[4]["gcover"])

                        await nonpbschannel.send(embed=embed)
                    else:
                        print(f"--- {key[0]} is an obsolete submission.")
                else:
                    print(f"--- {key[0]} has been rejected or deleted...")

                await local_submissionsdb.main(5,key[0])
    except Exception as exception:
        print(exception)

client.run(config.distoken, reconnect=True)