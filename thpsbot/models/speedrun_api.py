from typing import List

from pydantic import BaseModel, Field


class SRCVideosLinks(BaseModel):
    """Embedded model that holds SRC Video Links.

    Arguments:
        uri (str): URL of the video links.
    """

    uri: str


class SRCVideos(BaseModel):
    """Embedded model that holds SRC Videos.

    Arguments:
        links (List[SRCVideosLinks]): List of video links embedded in SRC speedruns.
    """

    links: List[SRCVideosLinks]


class SRCStatus(BaseModel):
    """Base model that holds SRC Run Status information.

    Arguments:
        status (str): The current status of the speedrun for approval.
        examiner (str | None): Unique ID of the player who approved the speedrun (can be `None`).
        verify_date (str | None): Approval date of the speedrun (can be `None).
    """

    status: str
    examiner: str | None = None
    verify_date: str | None = Field(default=None, alias="verify-date")


class SRCPlayers(BaseModel):
    """Base model that holds basic SRC Run Player information.

    Arguments:
        rel (str): The type of player in the SRC API (`user` or `guest`).
        id (str | None): If it is a real user, this is their unique ID.
        uri (str | None): If it is a real user, this is a link to their profile.
    """

    rel: str
    id: str | None = None
    uri: str | None = None


class SRCTimes(BaseModel):
    """Base model that holds SRC Run Times information.

    Arguments:
        primary (str): The time of the speedrun using the game's primary timing method.
        primary_t (float): The time of the speedrun using the game's primary timing method, as flaot
        realtime (str | None): The realtime timing for a speedrun.
        realtime_t (float): The realtime timing for a speedrun, as a float.
        realtime_noloads (str | None): The loads-removed time for a speedrun.
        realtime_noloads_t (float): The loads-removed time for a speedrun, as a float.
        ingame (str | None): The ingame time for a speedrun.
        ingame_t (float): The ingame time for a speedrun, as a float.
    """

    primary: str
    primary_t: float
    realtime: str | None
    realtime_t: float
    realtime_noloads: str | None
    realtime_noloads_t: float
    ingame: str | None
    ingame_t: float


class SRCSystem(BaseModel):
    """Embedded model that holds SRC Run System information.

    Arguments:
        platform (str): Unique ID of the associated platform.
        emulated (bool): If `True`, the speedrun was ran on an emulator.
        region (str): If given, it is the region the game was completed in.
    """

    platform: str
    emulated: bool
    region: str | None = None


class SRCLinks(BaseModel):
    """Embedded model that holds SRC Links information.

    Arguments:
        rel (str): The type of link that is being, uh, linked.
        uri (str): The direct link to what `rel` is referring to.
    """

    rel: str
    uri: str


class SRCRuns(BaseModel):
    """Base model that holds SRC Run information.

    Arguments:
        id (str): Unique ID of the speedrun.
        weblink (str): Direct link to the speedrun on SRC.
        game (str): Unique ID of the game.
        level (str): Unique ID of the level (if given).
        category (str): Unique category of the speedrun.
        videos (SRCVideos | None): A video or list of videos in a speedrun.
        comment (str | None): Comment left by the runner (or moderator) about the speedrun.
        status (SRCStatus): Status information about the speedrun.
        players (List[SRCPlayers]): A player or number of players in a list for the run.
        date (str): The simplified date the speedrun was submitted to SRC.
        submitted (str): The long-format date the speedrun was submitted to SRC.
        times (SRCTimes): List of times that was declared for the speedrun.
        splits (str | None): [DEPRECATED] Direct link to the splits file on splits.io.
        values (dict[str, str]): Dictionary item showing the variable:value pairs for the run.
        links (List[SRCLinks]): List of related links to the speedrun (e.g. game, category)
    """

    id: str
    weblink: str
    game: str
    level: str | None = None
    category: str
    videos: SRCVideos | None = None
    comment: str | None = None
    status: SRCStatus
    players: List[SRCPlayers]
    date: str
    submitted: str
    times: SRCTimes
    system: SRCSystem
    splits: str | None = None
    values: dict[str, str]
    links: List[SRCLinks]


class SRCNewRunsPagination(BaseModel):
    """Embedded model that holds SRC NewRuns Pagination.

    Arguments:
        offset (int): The positional offset within the API.
        max (int): The maximum number of returned entries from the endpoint.
        size (int): The number of returned results from the endpoint.
        links (list | None): Direct links to offsetted endpoints.
    """

    offset: int
    max: int
    size: int
    links: list | None = []


class SRCNewRuns(BaseModel):
    """Additional model that handles the new runs brought by SRC.

    Arguments:
        data (List[SRCRuns]): List of new speedruns within a game's endpoint.
        pagination (SRCNewRunsPagination):
    """

    data: List[SRCRuns]
    pagination: SRCNewRunsPagination
