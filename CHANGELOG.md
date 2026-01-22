## v3.5.2
###### January 22, 2026
*   Disabled `/awards clear`.
* * *


## v3.5.1
###### January 18, 2026
*   Fixed an issue where the wrong type was declared in `awards.py`, causing an error.
*   Fixed an issue where the connection to Discord could close and not re-open in time, causing a race condition.
    *   Now, it will gracefully catch it instead of crashing the cog.
* * *

## v3.5
###### January 18, 2026
*   Added the ability for streams to auto-publish in the selected livestream channel.
    *   If it is NOT an announcements channel, it will suppress the error (embed and role mention will still go through).
        *   This also counts the 10/hour rate limiting.
* * *

## v3.4.2
###### January 18, 2026
*   Added additional connection logic to `AIOHTTPHelper` that, when a site is inaccessible, will suppress the errors and warnings 20 times before raising a unique exception to Sentry.
* * *

## v3.4.1
###### January 17, 2026
*   Fixed an issue where there was a whitespace proceeding `Time` in the submission embed.
*   Fixed an issue where milliseconds were being truncated by the bot. [#23](https://github.com/thpsrun/THPSBot/issues/23)
* * *

## v3.4
###### January 17, 2026

### Added
*   Added proper type-checking and return typing to variables, objects, and functions when missed in previous verisons.

### Re-added
*   Re-added the "awards" emoji functionality (not retroactive), with the ability to set it via a command.
    *   All three of the below commands are admin-only:
    *   `/awards setreaction <REACTION>` will set the reaction to the award you chose.
    *   `/awards export` will export the messages currently "marked" via the reaction to a JSON file.
    *   `/awards clear` will export the JSON database and then clear it.
    *   `/awards status` shows the currently assigned reaction to "mark" messages and how many have been set.

### Updated
*   Updated libraries to their latest verison.
    *   Also updated Dockerfile binaries.

### Removed
*   Removed the ability to make public polls through the bot.
    *   If you click on the "+" icon on the left-side of Discord messages, you can make public polls that way. You can't see *who* voted for what, but you can see the percentage that way.


### Fixed
*   Fixed an issue where `Service Unavailable (503)` errors would completely break parts of the bot.
    *   Both background tasks and event listeners will make attempts to be better with Discord handling.

* * *

## v3.3.5
###### October 13, 2025
*   Fixed an issue where not having tags associated with a stream when attempting to find "NoSRL" would crash the livestream cog.

* * *

## v3.3.4
###### July 20, 2025
*   Added a check at startup so that, if the bot is in dev mode, it will not change bot avatars.
    *   I kept hitting the rate limit, lol.

*   Changed the public poll's parameters to say `oX_<name/emoji>` instead of `option1_name`.
    *   Helps keep this a bit more brief.

*   Fixed an issue where editing a poll's time would invoke a crash.
*   Fixed an issue where public polls requried the `time` parameter when it should've been optional.
*   Fixed an issue where the function in charge of syncing SRC run IDs and thps.run would crash if, after a run is verified or rejected, it would fail to remove the ID locally.
*   Fixed an issue where import runs to thps.run would return an error because I put a comma in the wrong spot.

* * *

## v3.3.3
###### July 18, 2025
*   Added an additional error handler for when `CommandNotFound` is invoked.
*   Added time delta to requested thps.run embeds.

*   Changed the `Placement` field for approved embeds so it displays both the place of the run and the number of players in that category.

*   Fixed an issue where only obsolete embeds would have points and placement displayed.
*   Fixed an issue where regular expression searches with a full SRC URL would return an error in some cases.

* * *

## v3.3.2
###### July 17, 2025
*   Fixed an issue where reactions wouldn't be cleared properly if the Discord member prevented direct messages after being granted a reaction role.
*   Fixed an issue where a reaction would be removed on the first attempt of adding reaction roles to a Discord message.

* * *

## v3.3.1
###### July 11, 2025
*   Added a configuration `.env` setting to determine when a Twitch embed would be "timed-out" and become offline/removed.
    *   Before, it was a hard-set 5 minutes. This is still the default, but now it is easily configurable instead of being hard-coded.

* * *

## v3.3
###### July 11, 2025
*   Added an additional field to Twitch Offline embeds that display the length of the stream.
*   Added a check to see if a stream is a marathon stream, thus getting less embedded buttons.
*   Added a check to streams that verify if it is streaming an approved game. If the `game_id` of the streamed game is not in the approved list, the offline countdown will begin.

* * *

## v3.2.1
###### July 8, 2025
*   Added error handling if Discord returns a 5XX HTTP code.
    *   This also covers the semi-rare `503 Service Unavailable` messages that Discord spits out every now and again.

* * *

## v3.2
###### July 7, 2025
*   Added buttons to stream embeds that will take you to the player's Twitch stream, Speedrun.com profile, or thps.run profile.
*   Changed Twitch embeds to compensate for new changes above.

* * *

## v3.1.0.3
###### June 30, 2025
*   Fixed an issue where, if thps.run's API returns `None` for the world record, it would return an error and crash.

* * *

## v3.1.0.2
###### June 28, 2025
*   Fixed an issue where, if thps.run's API returned a non-2XX HTTP response, it would result in an error when looking up games.

* * *

## v3.1.0.1
###### June 22, 2025
*   Fixed an issue where Twitch offline embedding would crash if the user did not have video archives enabled.

* * *

## v3.1.0
###### June 20, 2025
*   Added the `nickname` option to the `/thpsrun players` command.
    *   When successful, that player will be given the specified nickname.

*   Fixed an issue where commands were not properly syncing wiht the Discord API.

* * *

## v3.0.3.3
###### June 20, 2025
*   Fixed an issue where the additional check for `src.py` checking if SRC was down would not work properly.

## v3.0.3.2
###### June 18, 2025
*   Added an additional check to `streaming.py` to prevent issues where the thps.run API is down and causing a crash.
*   Added an additional check to `src.py` to prevent issues where the thps.run API is down and causing a crash.

* * *

## v3.0.3.1
###### June 18, 2025
*   Fixed an issue where `src.py` would return an error if the returned status message was not a 404 and not returning data.

* * *

## v3.0.3
###### June 18, 2025
*   Added an additional check to `src.py` to prevent `503: Service Unavailable` requests.

* * *

## v3.0.2
###### June 16, 2025
*   Added additional Sentry.io logging, especially for handled errors.
*   Added error handling for `ValueError` and `AttributeError`.
*   Updated bot's Docker image to 3.13.5-bookworm.

* * *

## v3.0.1
###### June 15, 2025
*   Fixed an issue where private polls were not saving properly and returning an error.
*   Fixed an issue where embeds were not being provided the `embed` field from the thps.run API, returning an error.
*   Fixed an issue where the URL to the user's profile on thps.run was not correct.
*   Fixed issue of renaming API URLs resulting in an error.

* * *

## v3.0
###### June 15, 2025

### Major Stuff
*   Refactored the entire project to use Discord.py again and use their Cogs/extensions system.
*   Utilizes Docker containers now.
*   Support to use thps.run's API with the `thpsrun.py` module.

### Added
*   Added support for public (reaction/emoji) and private (button) polls.
    *   Also added support for a report to be sent to the author's DMs upon the time expiring for the poll.
        *   If they cannot receive DMs or there are issues, the poll is posted in the channel.
*   Added the ability to dynamically create reaction:role pairings for specific messages (a lot like Reaction Roles bot).
    *   Doesn't support external emojis, obviously.
*   Added better error handling and reporting.
    *   Also uses Sentry.io if things get really weird.
*   Added better embed functionality and made better templates to pull from and edit.
*   Added the ability for streamers to "opt-out" of a specific stream IF they use "NoSRL" in their Twitch tags OR asking a global moderator to add them to the master exemptions list.
*   Added the ability to pull specific runs and their information from thps.run to show on the Discord.
*   Added the ability to pull specific player information from thps.run to show on the Discord.

### Changes
*   Changed the stream whitelist behavior to use thps.run's API (as in, if you have an approved run, you are on the whitelist).
    *   There is no "local" whitelist right now. A future update may add this.
    *   GamesDoneQuick and thps will be added as "users" to thps.run, so they will appear normally when they go live and play a Tony Hawk game.

### Fixed
*   Fixed an issue where, sometimes, the old bot would no longer send API PUT or POST requests to the thps.run API.

### Removed
*   (For the time being) therun.gg embed support has been removed.
    *   Need to figure out how to tie this in better with the new Cog system (probably make a new helper file).
*   Removed "side-game" support.
    *   This wasn't used very often and was turned off a long while ago without anyone noticing.
    *   If people want this again, I can make it happen later.

* * *

## Older Versions (v2)

## v2.0.5
*   Added the ability for moderators to add, remove, or query users to an "exemption" database.
    *   Runners in this database will not appear in the livestream bot channel.

## v2.0.4
*   Added support for automatically sending run approvals to the new thps.run API.

## v2.0.3.1
*   Fixed an issue where `aiosqlite` would improperly handle usernames upon deleting users.

## v2.0.3
*   Changed the behavior of `local_onlinedb.py` and `main.py` to add an additional check for livestream checks to ensure streams are actually offline.
    *   Originally, it would check Twitch's API every minute, but it could report an online if it wasn't.
    *   This new check will add a counter to streams; if the API says a stream is offline 5 times in a row, it will remove the embed and associated db entry.

## v2.0.2
*   Fixed an issue where runs awaiting for verification could break the script.
*   Changed the logic for when potential new additions are added to streamlist.db to avoid breaking submissions.

## v2.0.1
*   Fixed an issue where multiple streams would confuse the bot of which streamer was which.
*   Fixed an issue where deleting streams from the local database would fail.
*   Fixed an issue where therun.gg lookups would fail if the player skipped a split or if none was provided.
*   Fixed an issue where the emoji used for Tony's submissions failed to find the proper index if a message had more than 1 reaction.
*   Fixed an issue where errors would be returned if therun.gg does not return a HTTP Status 200.
*   Removed some obsolete modules.

## v2.0 - The CatBag Update
*   Added much better error handling and crash support.
*   Added the ability for admins to restart the entire bot.
*   Added the ability for admins to submit a new profile picture through the bot.
*   Added the ability for admins to force a new profile picture with /pfp.
*   Added the ability for admins to add new "Playing" messages through the bot.
*   Added the ability for mods and admins to automatically create polls with /poll.
*   Added the ability for all users to use an emote to submit a post/link for the Tony's.
*   Added therun.gg support; install the plugin and more fields will populate in the embed! :D
*   Added autocomplete functionality to some slash commands.

*   Changed bot usage to utilize slash commands; converted all previous commands.
*   Changed from using JSON to using SQLite3 databases (lmao).
*   Changed the livestream function to check the Twitch API every minute (previously every 5).
*   Changed the behavior of comments in Speedrun.com messages so links are not automatically clickable.

*   Recoded a lot of functions to become more asynchronous; should greatly increase speeds.

## v1.5.4
*   Added additional logic to deal with handheld ports of GBC, GBA, and PSP games.
*   Fixed an issue where the bot can crash if no role when embedding pending speedruns.
*   Fixed an issue where the bot doesn't know how to deal with IL speedruns with the new embedding format.

## v1.5.3
*   Added a timer so that the bot only begins at the 30 minute mark or at the start of the hour.
*   Added support for adding profile pictures dynamically, switched every 24 hours.
*   Added better code for Discord embeds using dictionaries and filling in details based on dynamic criteria.
*   Changed the the URL for clicking on someone's name in a PB/WR embed to link to their Speedrun.com profile.
*   Removed a lot of redundant code.
*   Fixed an issue where the bot would not report error messages in some situations.

## v1.5 *    The "Twitch Stream Lookups Don't Take Forever" Update
*   Added better error messages for troubleshooting purposes.
*   Changed how Twitch lookups were performed (instead of looking up for each user, it queries ALL approved games at once).
*   Fixed an issue where the bot could hang on Twitch lookups in rare circumstances.

## v1.4.7
*   Added support for THPS4 and THPS1+2 CE IL boards.

## v1.4.6
*   Added additional logic to prevent a possible infinite loop.
*   Fixed an issue where WR and PB times would both be incorrectly displayed in certain circumstances.
*   Fixed an issue where the delta against a current or past WR would sometimes be wrong.

## v1.4.5
*   Fixed an issue where the bot would not remove the stream ping after it has gone offline.
*   Fixed an issue where the bot would not properly parse verify*date from the /runs SRCOM API endpoint.

## v1.4.4
*   Added support for Discord members to opt into a "Strim" role to be notified of new streams.
*   Changed how the bot interprets times of prior WRs to reduce the amount of incorrect times.
*   Changed footer of submissions to reflect when the time was submitted and not time of posting.
*   Changed the SRCOM API interval to 20 minutes (from 30).

## v1.4.3
*   Added a secondary cache that logs runids for every approved speedrun to reduce duplicates.
*   Fixed an issue where all ILs were being associated with the THPS4 ILs Mod role.

## v1.4.2
*   Fixed an issue where the API requests would max out at 20 when querying the Tony Hawk series endpoint.

## v1.4.1
*   Added additional error handling checks to ensure the livestream routine would not crash.
*   Fixed an issue where usernames with special characters would crash the livestream routine.
*   Fixed an issue where approved players already on the stream whitelist would be duplicated.

## v1.4 - The Notifications Update
*   (Re*)Added support for game moderators to opt*in for notifications of submissions.
*   Added support for "unofficial" games to be displayed in #non*thps*pbs only if the user has an approved THPS run.
*   Added support for moderators and admins to add and remove "unofficial" games.
*   Added support for moderators to query list of all "unofficial" games the bot checks.
*   Changed the interval for checking Speedrun.com's API to 10 minutes (formerly 30, formerly 60).
    *   There is a chance that this might change to 15 minutes; still gathering some additional information to optimize this.
*   Fixed an issue where approved players would not be properly added to the stream whitelist.
*   Fixed an issue where WR delta would be incorrectly displayed.

## v1.3.2
*   Added support for Packle to have error logs properly sent.
*   Added additional logic to handle leaderboards without a world record on approval and tied world records for embeds.
*   Fixed an issue where WR and PB times were not being properly compared, resulting in weird deltas.
*   Fixed an issue where deleted runs would break script execution upon lookup.

## v1.3 - The "About Time" Update
*   Added platform and timing type (RTA, RTA w/o loads, or IGT) to the embeds for both game moderators and users in #pbs*and*clips.
*   Added information on number of completed runs by the player and last WR (if beaten) or current WR (if not) and the delta between for approved runs.
*   Added a comments field to the approved run embed that only displays if a comment exists.
*   Added workflow to check if a user is already whitelisted in livestreams and adds them if they do not appear.
*   Added "The Simpsons Skateboarding," "Matt Hoffman's Pro BMX," "Matt Hoffman's Pro BMX 2," and "Disney's Extreme Skate Adventure" to whitelisted games list.
*   Rewrote SRCOM API requests to consolidate number of API requests sent out.
*   Rewrote how sub*categories and level names were displayed to the game moderators channel.
*   Changed formula of THPSCE submissions to be a maximum of 10 points (formerly 100; displayed as 1000).
*   Changed checks for SRCOM submissions and approvals to occur every 30 minutes (formerly 1 hour).
*   Fixed an issue where stream thumbnails were cached and would not update properly.
