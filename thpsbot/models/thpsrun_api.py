from __future__ import annotations

from typing import Any, List

from pydantic import BaseModel


class THPSRunGame(BaseModel):
    id: str
    name: str
    slug: str
    release: str
    boxart: str | None = None
    twitch: str | None = None
    defaulttime: str
    idefaulttime: str
    pointsmax: int
    ipointsmax: int


class THPSRunCategory(BaseModel):
    id: str
    name: str
    slug: str | None = None
    type: str
    url: str | None = None
    rules: str | None = None
    appear_on_main: bool | None = None
    archive: bool | None = None


class THPSRunLevel(BaseModel):
    id: str
    name: str
    slug: str | None = None
    url: str | None = None


class THPSRunPlatform(BaseModel):
    id: str
    name: str
    slug: str | None = None


class THPSRunTimes(BaseModel):
    time: str | None = None
    time_secs: float | None = None
    timenl: str | None = None
    timenl_secs: float | None = None
    timeigt: str | None = None
    timeigt_secs: float | None = None
    p_time: str | None = None
    p_time_secs: float | None = None


class THPSRunPlayerInline(BaseModel):
    """Lightweight player object as it appears inside a run's `players` array."""

    id: str
    name: str
    url: str | None = None
    country: str | None = None
    pronouns: str | None = None
    twitch: str | None = None
    youtube: str | None = None
    twitter: str | None = None
    bluesky: str | None = None


class THPSRunRuns(BaseModel):
    id: str
    runtype: str
    place: int
    points: int | None = None
    obsolete: bool = False
    subcategory: str
    times: THPSRunTimes
    platform: str | THPSRunPlatform | None = None
    emulated: bool = False
    description: str | None = None
    video: str | None = None
    arch_video: str | None = None
    date: str | None = None
    v_date: str | None = None
    url: str
    resolved_primary_method: str | None = None
    resolved_required_methods: List[str] | None = None
    vid_status: str | None = None
    game: str | THPSRunGame | None = None
    category: str | THPSRunCategory | None = None
    level: str | THPSRunLevel | None = None
    players: List[THPSRunPlayerInline] = []
    variables: dict[str, str] | None = None


class RunImportIssues(BaseModel):
    id: str
    has_import_issues: bool = False
    import_issues: List[dict] = []


class CountrySchema(BaseModel):
    id: str
    name: str
    flag: str | None = None


class PlayerInfoEmbed(BaseModel):
    name: str
    nickname: str | None = None
    pronouns: str | None = None
    pfp: str | None = None
    ex_stream: bool = False
    country: CountrySchema | None = None


class PlayerSocialsSchema(BaseModel):
    twitch: str | None = None
    youtube: str | None = None
    twitter: str | None = None
    bluesky: str | None = None
    discord: str | None = None
    therun_gg: str | None = None


class PlayerStatsEmbed(BaseModel):
    total_runs: int | None = None
    fg_points: float | None = None
    il_points: float | None = None
    awards: list | None = None


class NameSlug(BaseModel):
    name: str | None = None
    slug: str | None = None


class PlayerRunInline(BaseModel):
    id: str
    game: NameSlug | None = None
    category: NameSlug | None = None
    subcategory: str | None = None
    level: NameSlug | None = None
    place: int | None = None
    points: int | None = None
    time: str | None = None
    date: str | None = None
    url: str | None = None
    video: str | None = None
    arch_video: str | None = None
    obsolete: bool | None = None
    value_slugs: List[str] | None = None


class PlayerRunsEmbed(BaseModel):
    recent: List[PlayerRunInline] | None = None
    fg: List[PlayerRunInline] | None = None
    il: List[PlayerRunInline] | None = None


class PlayerResponse(BaseModel):
    id: str
    url: str | None = None
    joined: str | None = None
    player: PlayerInfoEmbed
    socials: PlayerSocialsSchema | None = None
    stats: PlayerStatsEmbed | None = None
    runs: PlayerRunsEmbed | None = None


class PlayerSearchResult(BaseModel):
    id: str
    name: str
    nickname: str | None = None
    country_id: str | None = None
    pfp: str | None = None
    gradients: Any | None = None
