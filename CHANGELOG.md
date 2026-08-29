## v4.3
###### August 28, 2026
*   Added
    *   Added a check that, if either `DISCORD_PRIMARY_KEY` or `DISCORD_BETA_KEY` is not added to the proper mode, the bot auto-stops.
    *   Added an additional check to see if a record is tied. If so, it will display `(TWR)` instead of `(WR)`.
        *   This is an experimental fix to where, sometimes, if a run is tied it would display the wrong timeframe.

*   Fixed
    *   Fixed an issue where the bot would not properly perform initialization checks, resulting in a crash if the JSON files were not properly setup manually.
    *   Fixed an issue where the bot would write too many times for no real reason.
    *   Fixed an issue where the bot would update an offline embed, but then remove it at the max interval.
    *   Fixed an issue where checking Twitch names was not continually checked every run.
    *   Fixed an issue where, in some cases, the bot would get the wrong previous WR and interpret it incorrectly in the embeds.
        *   Also fixed this with v4.3 of the website, but this should help make it not as bad.
    *   Fixed an issue where the bot was using a Discord's `title` parameter instead of `description` for the name of the poll.
        *   Look, I'm an idiot.

*   Changed
    *   Changed the behavior of profile picture are handled in the Discord and within the bot.
    *   Changed the behavior of ading a Twitch.tv game to the lookup to allow admins the ability to add games to the whitelist.
        *   The bot should also be able to handle lookups a lot faster too.... maybe.
    *   Changed the behavior of the polls to make them more consistent.
        *   Re-wrote the functions a bit, since there were issues from pre-v4 I couldn't get around to with the latest releases.

* * *
## v4.2
###### June 7, 2026
*   Added time delta to the `Reign Duration` portion of approved embeds.
*   Added buttons to take you to Speedrun.com and thps.run (thps.run is now the default/first link seen).
    *   Submissions will take you to the thps.run or SRC hubs.

*   Fixed an issue where `approver` was not forwarded to the thps.run API, resulting in no approver being associated with the run.

* * *

## v4.1
###### June 6, 2026
*   Added a new `Reign Duration` function that, if a run is the WR, will show the length of time elapsed since the last WR.

* * *

## v4.0.3
###### June 3, 2026
*   Changed layout of how warnings appear in submission embeds.

* * *

## v4.0.2
###### June 3, 2026
*   Added links to the thps.run Submissions Hub and Speedrun.com for editing.
*   Fixed an issue where pfps were still not rendering properly (hopefully).

* * *

## v4.0.1
###### June 2, 2026
*   Fixed an issue where the returned `pfp` value of a player was appended to `THPS_RUN_API`, resulting in an error.

* * *

## v4.0
###### June 2, 2026
*   Added support for the new thps.run update.
    *   `/runs` and `/players` endpoints have been added.
*   Updated support for the bot to GET, POST, PUT, and DELETE to the thps.run `/streams` endpoint.
* * *