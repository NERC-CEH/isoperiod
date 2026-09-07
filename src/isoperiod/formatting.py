import datetime as dt

from isoperiod.enums import Precision
from isoperiod.exceptions import PeriodParsingError

# For use in datetime.isoformat()'s `timespec` argument.
TIMESPEC_MAP: dict[Precision, str] = {
    Precision.HOUR: "hours",
    Precision.MINUTE: "minutes",
    Precision.SECOND: "seconds",
    Precision.MILLISECOND: "milliseconds",
    Precision.MICROSECOND: "microseconds",
}


def format_naive(obj: dt.datetime, precision: Precision) -> str:
    """Format a naive datetime as an ISO 8601 string, to the given precision.

    Args:
        obj: The datetime object to be formatted. Any tzinfo it carries is ignored.
        precision: The finest time component to include in the output.

    Returns:
        The ISO 8601 string representation of the datetime

    Examples (for ``datetime(2024, 3, 1, 9, 30, 15, 123_456)``):
        .. code-block:: text

            Precision.DAY         -> "2024-03-01"
            Precision.MINUTE      -> "2024-03-01T09:30"
            Precision.MILLISECOND -> "2024-03-01T09:30:15.123"
    """
    if precision == Precision.YEAR:
        return f"{obj.year:04}"
    if precision == Precision.MONTH:
        return f"{obj.year:04}-{obj.month:02}"
    if precision == Precision.DAY:
        return obj.date().isoformat()
    return obj.replace(tzinfo=None).isoformat(timespec=TIMESPEC_MAP[precision])


def format_aware(obj: dt.datetime, precision: Precision) -> str:
    """Format a timezone-aware datetime as an ISO 8601 string, to the given precision.

    Unlike `format_naive`, this never formats coarser than HOUR: a bare date cannot carry a UTC offset in ISO 8601,
    so the output always includes at least the hour to keep the offset visible. Any precision coarser than HOUR is
    treated as HOUR.

    Args:
        obj: The datetime object to be formatted.
        precision: The finest time component to include in the output.

    Returns:
        The ISO 8601 string representation of the datetime, e.g. (at SECOND
        precision) yyyy-mm-ddThh:mm:ss{tz}

    Examples (for ``datetime(2024, 3, 1, 9, 30, 15, tzinfo=tz)``):
        .. code-block:: text

            tz = UTC,     Precision.SECOND -> "2024-03-01T09:30:15Z"
            tz = +05:30,  Precision.HOUR   -> "2024-03-01T09+05:30"
            tz = +05:30,  Precision.DAY    -> "2024-03-01T09+05:30"  (coarser than HOUR is clamped)
    """
    timespec = TIMESPEC_MAP.get(precision, "hours")
    naive_part = obj.replace(tzinfo=None).isoformat(timespec=timespec)
    return naive_part + format_tzinfo(obj.tzinfo)


def format_tzdelta(delta: dt.timedelta) -> str:
    """Convert a timedelta which represents a timezone to a string that represents that timezone

    Args:
        delta: The timedelta

    Returns:
        A string that can be used to represent a timezone in an ISO 8601 format string

    Examples:
        .. code-block:: text

            timedelta(0)                    -> "Z"
            timedelta(hours=5, minutes=30)  -> "+05:30"
            timedelta(hours=-5)             -> "-05:00"
    """
    try:
        name = dt.timezone(delta).tzname(None)
    except ValueError as err:
        raise PeriodParsingError(f"Illegal tz delta: {delta}. Amount of time must be less than 1 day.") from err
    return name.removeprefix("UTC") or "Z"


def format_tzinfo(tz: dt.tzinfo | None) -> str:
    """Convert an optional tzinfo object into a string that
    can be used to represent the timezone in an ISO 8601 format

    Args:
        tz: The tzinfo object, or None

    Returns:
        A string that can be used to represent a timezone
        in an ISO 8601 format string

    Examples:
        .. code-block:: text

            None                                        -> ""
            timezone.utc                                -> "Z"
            timezone(timedelta(hours=-3, minutes=-30))  -> "-03:30"
    """
    if tz is not None:
        delta = tz.utcoffset(dt.datetime.min)
        if delta is not None:
            return format_tzdelta(delta)
    return ""
