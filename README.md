# THPSBot v2.0

## What is this!?
THPSBot is a bot for the [THPS Speedrun Discord](https://thps.run/discord). It is a bot specially designed by [ThePackle](https://twitter.com/thepackle) that combines multiple functions. This includes:
* Periodic checks to the [Speedrun.com API](https://github.com/speedruncomorg/api) to see if there is any new games to verify in the THPS series.
* Checks every minute to see if someone is currently streaming.
  * If they have therun.gg LiveSplit plugin, there is more data added to their stream embed!!
* And a lot more, specially designed for community. :)

## Note About This Repo
**This is a bot specially created for the THPS community, so there is a LOT that is curated for us.** This project is available to everyone to look at/tinker with/review. I __will not__ be giving any instructions on how to set it up, so it will require some tinkering and knowledge of Python to use.

## Changelog

### v2.0.3.1
- Fixed an issue where `aiosqlite` would improperly handle usernames upon deleting users.

### v2.0.3
- Changed the behavior of `local_onlinedb.py` and `main.py` to add an additional check for livestream checks to ensure streams are actually offline.
  - Originally, it would check Twitch's API every minute, but it could report an online if it wasn't.
  - This new check will add a counter to streams; if the API says a stream is offline 5 times in a row, it will remove the embed and associated db entry.

### v2.0.2
- Fixed an issue where runs awaiting for verification could break the script.
- Changed the logic for when potential new additions are added to streamlist.db to avoid breaking submissions.

### v2.0.1
- Fixed an issue where multiple streams would confuse the bot of which streamer was which.
- Fixed an issue where deleting streams from the local database would fail.
- Fixed an issue where therun.gg lookups would fail if the player skipped a split or if none was provided.
- Fixed an issue where the emoji used for Tony's submissions failed to find the proper index if a message had more than 1 reaction.
- Fixed an issue where errors would be returned if therun.gg does not return a HTTP Status 200.
- Removed some obsolete modules.

### v2.0 - The CatBag Update
- Added much better error handling and crash support.
- Added the ability for admins to restart the entire bot.
- Added the ability for admins to submit a new profile picture through the bot.
- Added the ability for admins to force a new profile picture with /pfp.
- Added the ability for admins to add new "Playing" messages through the bot.
- Added the ability for mods and admins to automatically create polls with /poll.
- Added the ability for all users to use an emote to submit a post/link for the Tony's.
- Added therun.gg support; install the plugin and more fields will populate in the embed! :D
- Added autocomplete functionality to some slash commands.

- Changed bot usage to utilize slash commands; converted all previous commands.
- Changed from using JSON to using SQLite3 databases (lmao).
- Changed the livestream function to check the Twitch API every minute (previously every 5).
- Changed the behavior of comments in Speedrun.com messages so links are not automatically clickable.

- Recoded a lot of functions to become more asynchronous; should greatly increase speeds.

### v1.5.4
- Added additional logic to deal with handheld ports of GBC, GBA, and PSP games.
- Fixed an issue where the bot can crash if no role when embedding pending speedruns.
- Fixed an issue where the bot doesn't know how to deal with IL speedruns with the new embedding format.

### v1.5.3
- Added a timer so that the bot only begins at the 30 minute mark or at the start of the hour.
- Added support for adding profile pictures dynamically, switched every 24 hours.
- Added better code for Discord embeds using dictionaries and filling in details based on dynamic criteria.
- Changed the the URL for clicking on someone's name in a PB/WR embed to link to their Speedrun.com profile.
- Removed a lot of redundant code.
- Fixed an issue where the bot would not report error messages in some situations.

### v1.5 - The "Twitch Stream Lookups Don't Take Forever" Update
- Added better error messages for troubleshooting purposes.
- Changed how Twitch lookups were performed (instead of looking up for each user, it queries ALL approved games at once).
- Fixed an issue where the bot could hang on Twitch lookups in rare circumstances.

### v1.4.7
- Added support for THPS4 and THPS1+2 CE IL boards.

### v1.4.6
- Added additional logic to prevent a possible infinite loop.
- Fixed an issue where WR and PB times would both be incorrectly displayed in certain circumstances.
- Fixed an issue where the delta against a current or past WR would sometimes be wrong.

### v1.4.5
- Fixed an issue where the bot would not remove the stream ping after it has gone offline.
- Fixed an issue where the bot would not properly parse verify-date from the /runs SRCOM API endpoint.

### v1.4.4
- Added support for Discord members to opt into a "Strim" role to be notified of new streams.
- Changed how the bot interprets times of prior WRs to reduce the amount of incorrect times.
- Changed footer of submissions to reflect when the time was submitted and not time of posting.
- Changed the SRCOM API interval to 20 minutes (from 30).

## v1.4.3
- Added a secondary cache that logs runids for every approved speedrun to reduce duplicates.
- Fixed an issue where all ILs were being associated with the THPS4 ILs Mod role.

### v1.4.2
- Fixed an issue where the API requests would max out at 20 when querying the Tony Hawk series endpoint.

### v1.4.1
- Added additional error handling checks to ensure the livestream routine would not crash.
- Fixed an issue where usernames with special characters would crash the livestream routine.
- Fixed an issue where approved players already on the stream whitelist would be duplicated.

### v1.4 - The Notifications Update
- (Re-)Added support for game moderators to opt-in for notifications of submissions.
- Added support for "unofficial" games to be displayed in #non-thps-pbs only if the user has an approved THPS run.
- Added support for moderators and admins to add and remove "unofficial" games.
- Added support for moderators to query list of all "unofficial" games the bot checks.
- Changed the interval for checking Speedrun.com's API to 10 minutes (formerly 30, formerly 60).
-- There is a chance that this might change to 15 minutes; still gathering some additional information to optimize this.
- Fixed an issue where approved players would not be properly added to the stream whitelist.
- Fixed an issue where WR delta would be incorrectly displayed.

### v1.3.2
- Added support for Packle to have error logs properly sent.
- Added additional logic to handle leaderboards without a world record on approval and tied world records for embeds.
- Fixed an issue where WR and PB times were not being properly compared, resulting in weird deltas.
- Fixed an issue where deleted runs would break script execution upon lookup.

### v1.3 - The "About Time" Update
- Added platform and timing type (RTA, RTA w/o loads, or IGT) to the embeds for both game moderators and users in #pbs-and-clips.
- Added information on number of completed runs by the player and last WR (if beaten) or current WR (if not) and the delta between for approved runs.
- Added a comments field to the approved run embed that only displays if a comment exists.
- Added workflow to check if a user is already whitelisted in livestreams and adds them if they do not appear.
- Added "The Simpsons Skateboarding," "Matt Hoffman's Pro BMX," "Matt Hoffman's Pro BMX 2," and "Disney's Extreme Skate Adventure" to whitelisted games list.
- Rewrote SRCOM API requests to consolidate number of API requests sent out.
- Rewrote how sub-categories and level names were displayed to the game moderators channel.
- Changed formula of THPSCE submissions to be a maximum of 10 points (formerly 100; displayed as 1000).
- Changed checks for SRCOM submissions and approvals to occur every 30 minutes (formerly 1 hour).
- Fixed an issue where stream thumbnails were cached and would not update properly.
