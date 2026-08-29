import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# Naturalizes it to the America/New_York timezone, so the timestamps are locked to one specific zone
BOT_TIMEZONE = ZoneInfo("America/New_York")

# Discord caps embed titles at 256 chars and channel/thread names at 100.
TITLE_LIMIT = 256
THREAD_NAME_LIMIT = 100

_TIMESTAMP_RE = re.compile(r"<t:(\d+)(?::[a-zA-Z])?>")

_END_TIME_RE = re.compile(
    r"(?:This|The) poll ends at <t:\d+(?::[a-zA-Z])?>(?: \(updated\))?"
)


def parse_timestamp(
    time: str,
) -> tuple[datetime, str] | None:
    """Parse a bare Discord timestamp tag into a local datetime and normalized tag.

    Arguments:
        time (str): A Discord timestamp tag, e.g. `<t:1700000000:F>` or
            `<t:1700000000>`; surrounding whitespace is ignored.

    Returns:
        parsed (tuple[datetime, str] | None): `(local_time, long_tag)` where local_time (datetime)
            is the instant of `BOT_TIMEZONE` and long_tag (str) is the canonical `<t:...:F>` form;
            `None` when the input is not a well-formed, bare timestamp tag or is out of range.
    """
    matched = _TIMESTAMP_RE.fullmatch(time.strip())
    if not matched:
        return None

    timestamp = int(matched.group(1))
    try:
        utc_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None

    local_time = utc_dt.astimezone(BOT_TIMEZONE)
    long_tag = f"<t:{timestamp}:F>"
    return local_time, long_tag


def truncate_thread_name(
    message: str,
    suffix: str = " - Discussion",
) -> str:
    """Build a thread name that stays within Discord's 100-char name cap.

    Arguments:
        message (str): The poll question used as the thread-name prefix.
        suffix (str): The text appended after the message (default `" - Discussion"`).
    """
    available = THREAD_NAME_LIMIT - len(suffix)
    if available <= 0:
        return suffix[:THREAD_NAME_LIMIT]

    return message[:available] + suffix


def truncate_title_suffix(
    title: str,
    suffix: str,
) -> str:
    """Append a suffix to an embed title without exceeding Discord's 256-char cap.

    Arguments:
        title (str): The current embed title.
        suffix (str): The suffix to append, e.g. `" (ENDED)"`.
    """
    available = TITLE_LIMIT - len(suffix)
    if available <= 0:
        return suffix[:TITLE_LIMIT]

    return title[:available] + suffix


def summarize_votes(
    options: list[str],
    votes: dict[str, str],
) -> str:
    """Tally button-poll votes into a per-option breakdown.

    Arguments:
        options (list[str]): The poll's option labels, in display order.
        votes (dict[str, str]): Mapping of voter id (str) to their chosen label.
    """
    counts = {opt: 0 for opt in options}
    for choice in votes.values():
        if choice in counts:
            counts[choice] += 1

    return "\n".join(f"**{opt}** - {n}" for opt, n in counts.items())


def replace_end_time(
    description: str,
    long_tag: str,
) -> str:
    """Rewrite a poll's "ends at" line to a new timestamp, marked as updated.


    Arguments:
        description (str): The current embed description.
        long_tag (str): The new canonical `<t:...:F>` timestamp tag.

    Returns:
        updated (str): The description with the end-time line pointing at the new
            timestamp and a single trailing `(updated)` marker.
    """
    return _END_TIME_RE.sub(f"This poll ends at {long_tag} (updated)", description)
