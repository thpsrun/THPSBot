import discord,configparser,asyncio
from discord.ext import commands

config = configparser.ConfigParser()
config.read("./config.ini")
configdiscord = config["Discord"]

intents = discord.Intents.default()
client = commands.Bot(command_prefix=configdiscord["prefix"], intents=intents, help_command=None)

@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

@client.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def countdown(ctx,user: discord.Member,user2: discord.Member,arg3,arg4,arg5):
    if ctx.channel.name != "s2-match":
        return

    timer = int(arg3) * 60 + 60
    timer2 = int(arg4) * 60 + 60

    cdtimer = 0

    if arg4 == "mute":
        await user.edit(mute=True)
        await user2.edit(mute=True)
    elif arg4 == "deafen":
        await user.edit(deafen=True)
        await user2.edit(deafen=True)
        await user.edit(mute=True)
        await user2.edit(mute=True)


    if timer == timer2:
        await ctx.send("COUNTDOWN BEGINNING! {0} MINUTES IN THE ROUND!".format(arg3))
    else:
        await ctx.send("COUNTDOWN BEGINNING! {0} MINUTES IN THE ROUND FOR {1}!".format(arg3,user))
        await ctx.send("COUNTDOWN BEGINNING! {0} MINUTES IN THE ROUND FOR {1}!".format(arg4,user2))

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    stopped = False
    while cdtimer <= 4:
        if cdtimer == 0: await ctx.send("GET READY...")
        elif cdtimer == 2: await ctx.send("GET SET...")
        elif cdtimer == 4: await ctx.send("GO! {0} {1}".format(user.mention,user2.mention))
        cdtimer += 1
        timer -= 1
        await asyncio.sleep(1)

    while (timer >= 0 or timer2 >= 0) and not stopped:
        try:
            message = await client.wait_for("message", check=check, timeout=0)
            stopped = True if message.content.lower() == "!stop" else False
        except asyncio.TimeoutError:
            if arg3 == arg4:
                if timer == 360: await ctx.send("{0} {1} - 5 MINUTE WARNING".format(user.mention,user2.mention))
                if timer == 180: await ctx.send("{0} {1} - 2 MINUTE WARNING".format(user.mention,user2.mention))
                if timer == 63: await ctx.send("TIME STOPS IN 3...")
                if timer == 62: await ctx.send("2...")
                if timer == 61: await ctx.send("1...")
                if timer == 60: await ctx.send("{0} {1} - OVERTIME! Finish your current run!".format(user.mention,user2.mention))
                if timer == 0:
                    if arg4 == "mute":
                        await user.edit(mute=False)
                        await user2.edit(mute=False)
                    else:
                        await user.edit(deafen=False)
                        await user2.edit(deafen=False)
                        await user.edit(mute=False)
                        await user2.edit(mute=False)
                    
                timer -= 1
            else:
                if timer == 360: await ctx.send("{0} - 5 MINUTE WARNING".format(user.mention))
                if timer2 == 360: await ctx.send("{0} - 5 MINUTE WARNING".format(user2.mention))

                if timer == 180: await ctx.send("{0} - 2 MINUTE WARNING".format(user.mention))
                if timer2 == 180: await ctx.send("{0} - 2 MINUTE WARNING".format(user2.mention))

                if timer == 63: await ctx.send("TIME STOPS FOR {0} IN 3...".format(user.mention))
                if timer == 62: await ctx.send("2...")
                if timer == 61: await ctx.send("1...")
                if timer == 60: await ctx.send("{0} - OVERTIME! Finish your current run!".format(user.mention))
                
                if timer2 == 63: await ctx.send("TIME STOPS FOR {0} IN 3...".format(user2.mention))
                if timer2 == 62: await ctx.send("2...")
                if timer2 == 61: await ctx.send("1...")
                if timer2 == 60: await ctx.send("{0} - OVERTIME! Finish your current run!".format(user2.mention))
    
                timer -= 1
                timer2 -= 1

        await asyncio.sleep(1)

    if stopped == True:
        await ctx.send("COUNTDOWN STOPPED")
    else:
        await ctx.send("COUNTDOWN COMPLETE")

        await user.edit(deafen=False)
        await user2.edit(deafen=False)
        await user.edit(mute=False)
        await user2.edit(mute=False)

client.run(configdiscord["distoken"])
