from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta


def _join_parts(
    parts: list[tuple[int, str]],
) -> str:
    """Comma-join non-zero (value, singular-unit) pairs, pluralized."""
    rendered = [
        f"{value} {unit}" if value == 1 else f"{value} {unit}s"
        for value, unit in parts
        if value
    ]
    return ", ".join(rendered)


def format_reign(
    start: datetime,
    end: datetime,
) -> str:
    """Lowercase length of a world-record reign from ``start`` to ``end``.

    >= 1 day -> "3 years, 3 months, 2 days"
    < 1 day  -> "5 hours, 12 minutes" / "less than a minute"
    """
    delta = end - start
    rd = relativedelta(end, start)

    if delta < timedelta(days=1):
        phrase = _join_parts([(rd.hours, "hour"), (rd.minutes, "minute")])
        return phrase or "less than a minute"

    return _join_parts([(rd.years, "year"), (rd.months, "month"), (rd.days, "day")])


def format_gap(
    seconds: float,
) -> str:
    """Compact 'Xh Ym Zs Wms' magnitude of a delta, dropping zero parts ("" if zero)."""
    total_ms = int(round(abs(seconds) * 1000))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    parts = [
        f"{value}{suffix}"
        for value, suffix in ((hours, "h"), (minutes, "m"), (secs, "s"), (ms, "ms"))
        if value
    ]
    return " ".join(parts)
