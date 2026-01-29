from __future__ import annotations

from typing import List

from pydantic import BaseModel


# BASE MODELS #
class THPSRunGame(BaseModel):
    """Embedded model that holds thps.run Game information.

    Arguments:
        id (str): Unique game ID.
        name (str): The name of the game.
        slug (str): Slugified version of the name for easier URL access.
        release (str): Release date of the game.
        boxart (str | None): Boxart data stored on SRC's website.
        defaulttime (str): The default timing method of the game.
        idefaulttime (str): The default timing method of the ILs in the game.
        pointsmax (int): Maximum number of points a world record is given in a game.
        ipointsmax (int): Maximum number of points an IL world record is given in a game.
    """

    id: str
    name: str
    slug: str
    release: str
    boxart: str | None
    twitch: str | None
    defaulttime: str
    idefaulttime: str
    pointsmax: int
    ipointsmax: int


class THPSRunCategory(BaseModel):
    """Embedded model that holds thps.run Category information.

    Arguments:
        id (str): Unique category ID.
        name (str): The name of the category.
        type (str): The type of category (e.g. per-level, per-game).
        url (str): Speedrun.com URL.
        hidden (str): Categories marked as hidden are hidden from all records.
    """

    id: str
    name: str
    type: str
    url: str
    archive: bool


class THPSRunLevel(BaseModel):
    """Embedded model that holds thps.run Level information.

    Arguments:
        id (str): Unique level ID.
        name (str): The name of the level.
        url (str): Speedrun.com URL.
    """

    id: str
    name: str
    url: str


# VARIABLE MODELS #
class THPSRunVariableValue(BaseModel):
    """Embedded model that holds thps.run VariableValues information.

    Arguments:
        value (str): Unique value ID.
        name (str): The name of the value.
        hidden (str): Values marked as hidden are hidden from all records.
        variable (str): The unique ID of the linked variable.
    """

    value: str
    name: str
    hidden: bool
    variable: str


class THPSRunVariable(BaseModel):
    """Base model that holds thps.run Variable information.

    Arguments:
        name (str): Name of the variable.
        cat (str | None): The unique ID of the linked category.
        all_cats (bool): When true, it is a global category.
        scope (str): The scope of the category (e.g. full-game).
        hidden (str): Variables marked as hidden are hidden from all records.
        values (THPSRunVariableValue): Embedded information that details the values.
    """

    name: str
    cat: str | None = None
    all_cats: bool
    scope: str
    hidden: bool
    values: THPSRunVariableValue


# PLAYER MODELS #
class THPSRunPlayerAwards(BaseModel):
    """Embedded model that holds thps.run Player Awards information.

    Arguments:
        name (str): The name of the award.
    """

    name: str


class THPSRunPlayerStats(BaseModel):
    """Embedded model that holds thps.run Player Stats information.

    Arguments:
        total_pts (int): Total amount of points the player has.
        main_pts (int): Total amount of points the player has in full-game runs.
        il_pts (int): Total amount of points the player has in all IL runs.
        total_runs (int): Total number of runs within the database.
    """

    total_pts: int
    main_pts: int
    il_pts: int
    total_runs: int


class THPSRunPlayers(BaseModel):
    """Base model that holds thps.run Players information.

    Arguments:
        id (str): Unique ID of the player.
        name (str): Name of the player.
        nickname (str | None): Optional name of the player that takes precedent over `name`.
        url (str): Speedrun.com URL to the player's profile.
        pfp (str | None): Relative link to the player's profile picture on thps.run.
        country (str | None): Country name the player has marked to belong to.
        pronouns (str | None): Pronouns of the player.
        twitch (str | None): Linked Twitch.tv profile of the player.
        youtube (str | None): Linked YouTube profile of the player.
        twitter (str | None): Linked Twitter profile of the player.
        ex_stream (bool): When true, the player will not show up in livestream views.
        awards (List[THPSRunPlayerAwards] | None): List of awards the player has accumulated.
        stats (THPSRnPlayerStats): Statistics of the player from thps.run.
    """

    id: str
    name: str
    nickname: str | None = None
    url: str
    pfp: str | None = None
    country: str | None = None
    pronouns: str | None = None
    twitch: str | None = None
    youtube: str | None = None
    twitter: str | None = None
    ex_stream: bool
    awards: List[THPSRunPlayerAwards] | None = None
    stats: THPSRunPlayerStats


# RUN MODELS #
class THPSRunTimes(BaseModel):
    """Embedded model that holds thps.run Run Time information.

    Arguments:
        defaulttime (str): The default timing method the run follows.
        time (str | None): String version of `time_secs` in Xh YYm ZZs formatting.
        time_secs (float | None): Float time for realtime (RTA) runs.
        timenl (str | None): String version of `timenl_secs` in Xh YYm ZZs formatting.
        timenl_secs (float | None): Float time for realtime no loads (LRT) runs.
        timeigt (str | None): String version of `timeigt_secs` in Xh YYm ZZs formatting.
        timeigt_secs (float | None): Float time for in-game time (IGT) runs.
    """

    defaulttime: str
    time: str | None = None
    time_secs: float | None = None
    timenl: str | None = None
    timenl_secs: float | None = None
    timeigt: str | None = None
    timeigt_secs: float | None = None


class THPSRunSystemPlatform(BaseModel):
    """Embedded model that holds thps.run Platform information.

    Arguments:
        id (str): Unique platform ID.
        name (str): The name of the platform.
    """

    id: str
    name: str


class THPSRunSystem(BaseModel):
    """Embeded model that holds thps.run System information.

    Arguments:
        platform (str | THPSRunSystemPlatform): Either the unique ID of the platform or its
            embeded information.
        emulated (bool): When true, the run is on an approved emulator.
    """

    platform: str | THPSRunSystemPlatform
    emulated: bool


class THPSRunStatus(BaseModel):
    """Embedded model that holds thps.run Status information.

    Arguments:
        vid_status (str): The status of the run (e.g. verified, denied).
        approver (str | None): The unique ID of the player who approved the run.
        v_date (str): The date the run was verified and approved.
        obsolete (bool): When true, the run is obsolete and a better time exists.
    """

    vid_status: str
    approver: str | None = None
    v_date: str | None = None
    obsolete: bool


class THPSRunVideos(BaseModel):
    """Embedded model that holds thps.run Run Video information.

    Arguments:
        video (str | None): The direct URL of the speedrun video.
        arch_video (str | None): Special field meant to hold archived video information on
            an external platform.
    """

    video: str | None = None
    arch_video: str | None = None


class THPSRunMeta(BaseModel):
    """Embedded model that holds thps.run Run Meta information.

    Arguments:
        points (int): How many points the run is worth, if it is not obsolete.
        url (int): Speedrun.com link to the run.
    """

    points: int
    url: str


class THPSRunRuns(BaseModel):
    """Base model that holds thps.run Run information.

    Arguments:
        id (str): Unique ID of the run.
        runtype (str): Marks whether the run is full-game (`main`) or an IL (`il`).
        game (str | THPSRunGame): The embedded game information on a speedrun.
        category (str | THPSRunCategory): The embedded category information on a speedrun.
        level (str | THPSRunLevel): The embedded level information on a speedrun.
        subcategory (str): Full name of the subcategory of the speedrun.
        place (int): If not obsolete, the place on the leaderboard the run is in.
        lb_count (int): The returned value of how many approved and non-obsolete runs exist on that
            run's leaderboard.
        players (str | THPSRunPlayers): The embedded player information on a speedrun.
        date (str | None): The date the run was submitted to Speedrun.com.
        record (THPSRunRuns): The embedded record information on a speedrun.
        times (THPSRunTimes): Embedded information about the run's timings.
        system (THPSRunSystem): Embedded information about the run's platform.
        status (THPSRunStatus): Embedded information about the run's status.
        videos (THPSRunVideos): Embedded information about the run's videos and archives.
        variables (dict[str, str] | dict[str, THPSRunVariable] | None): Either the unique
            variable:value ID pairs or its embedded information.
        meta (THPSRunMeta): Embedded information about the run's meta information.
        description (str | None): The run's comments from the runner.
    """

    id: str
    runtype: str
    game: str | THPSRunGame
    category: str | THPSRunCategory
    level: str | THPSRunLevel | None = None
    subcategory: str
    place: int
    lb_count: int
    players: str | THPSRunPlayers | List[THPSRunPlayers]
    date: str | None = None
    record: str | THPSRunRuns | None = None
    times: THPSRunTimes
    system: str | THPSRunSystem
    status: THPSRunStatus
    videos: THPSRunVideos
    variables: dict[str, str] | dict[str, THPSRunVariable] | None = None
    meta: THPSRunMeta
    description: str | None = None


class THPSRunNewRuns(BaseModel):
    """Additional model that handles the new runs brought by thps.run.

    Arguments:
        new_runs (List[THPSRunRuns]): List of new speedruns within a game's endpoint.
    """

    new_runs: List[THPSRunRuns]


# PERSONAL BEST MODEL #
class THPSRunPBs(THPSRunPlayers):
    main_runs: List[THPSRunRuns] | None = None
    il_runs: List[THPSRunRuns] | None = None
