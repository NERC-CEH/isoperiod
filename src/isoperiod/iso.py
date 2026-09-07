"""Helpers for building ISO 8601 duration strings and the regex fragment used to parse ISO 8601 durations."""


def period_regex(prefix: str) -> str:
    """Return a regular expression string for matching an ISO 8601 duration (but without the initial "P" character)

    Args:
        prefix: The name prefix used for Python regex group names

    Returns:
        A string containing a regular expression that can be used to parse an ISO 8601 duration
    """
    return (
        rf"(?:(?P<{prefix}_years>\d+)[Yy])?"
        rf"(?:(?P<{prefix}_months>\d+)[Mm])?"
        rf"(?:(?P<{prefix}_days>\d+)[Dd])?"
        r"(?:[Tt]?"
        rf"(?:(?P<{prefix}_hours>\d+)[Hh])?"
        rf"(?:(?P<{prefix}_minutes>\d+)[Mm])?"
        rf"(?:(?P<{prefix}_seconds>\d+)"
        rf"(?:\.(?P<{prefix}_microseconds>\d{{1,6}}))?"
        r"[Ss])?"
        r")?"
    )


def second_string(seconds: int, microseconds: int) -> str:
    """Convert seconds and microseconds (0-999_999) to a string that can be used to format an ISO 8601 duration string.

    Args:
        seconds: The number of seconds
        microseconds: The number of microseconds

    Returns:
        A string representing seconds and microseconds that can be used in an ISO 8601 duration string

    Examples:
        .. code-block:: text

            second_string(30, 0)       -> "30"
            second_string(1, 500_000)  -> "1.5"     (trailing zeros trimmed)
            second_string(10, 123_400) -> "10.1234"
    """
    if microseconds == 0:
        return str(seconds)
    return f"{seconds}.{microseconds:06}".rstrip("0")


def append_second_elems(elems: list[str], seconds: int, microseconds: int) -> list[str]:
    """Append total seconds and microseconds to a list of strings that, when joined, produce an ISO 8601 duration
    string.

    Args:
        elems: The list of strings
        seconds: The number of seconds
        microseconds: The number of microseconds

    Returns:
        The amended list of strings

    Examples (joining the result of appending onto ``["P"]``):
        .. code-block:: text

            append_second_elems(["P"], 90, 0)      -> "PT1M30S"
            append_second_elems(["P"], 90_061, 0)  -> "P1DT1H1M1S"
            append_second_elems(["P"], 0, 500_000) -> "PT0.5S"
    """
    days, seconds_in_day = divmod(seconds, 86_400)
    if days > 0:
        elems.append(f"{days}D")
    if (seconds_in_day > 0) or (microseconds > 0):
        elems.append("T")
        hours, seconds_in_hour = divmod(seconds_in_day, 3_600)
        if hours > 0:
            elems.append(f"{hours}H")
        minutes, seconds_in_minute = divmod(seconds_in_hour, 60)
        if minutes > 0:
            elems.append(f"{minutes}M")
        if (seconds_in_minute > 0) or (microseconds > 0):
            elems.append(second_string(seconds_in_minute, microseconds))
            elems.append("S")
    return elems


def append_month_elems(elems: list[str], months: int) -> list[str]:
    """Append total number of months to a list of strings that, when joined, produce an ISO 8601 duration string.

    Args:
        elems: The list of strings
        months: The total number of months

    Returns:
        The amended list of strings

    Examples (joining the result of appending onto ``["P"]``):
        .. code-block:: text

            append_month_elems(["P"], 6)  -> "P6M"
            append_month_elems(["P"], 13) -> "P1Y1M"
    """
    years, months_in_year = divmod(months, 12)
    if years > 0:
        elems.append(f"{years}Y")
    if months_in_year > 0:
        elems.append(f"{months_in_year}M")
    return elems


def microsecond_period_name(total_microseconds: int) -> str:
    """Return an ISO 8601 duration string from a total number of microseconds in a period.

    Args:
        total_microseconds: The total number of microseconds

    Returns:
        The ISO 8601 duration string representing a period
        of n-microseconds

    Examples:
        .. code-block:: text

            microsecond_period_name(1)         -> "PT0.000001S"
            microsecond_period_name(1_500_000) -> "PT1.5S"
    """
    seconds, microseconds = divmod(total_microseconds, 1_000_000)
    return "".join(append_second_elems(["P"], seconds, microseconds))


def second_period_name(seconds: int) -> str:
    """Return an ISO 8601 duration string from a total number of seconds in a period.

    Args:
        seconds: The total number of seconds

    Returns:
        The ISO 8601 duration string representing a period
        of n-seconds

    Examples:
        .. code-block:: text

            second_period_name(3_600)  -> "PT1H"
            second_period_name(86_400) -> "P1D"
    """
    return "".join(append_second_elems(["P"], seconds, 0))


def month_period_name(months: int) -> str:
    """Return an ISO 8601 duration string from a total number of months in a period.

    Args:
        months: The total number of months

    Returns:
        The ISO 8601 duration string representing a period
        of n-months

    Examples:
        .. code-block:: text

            month_period_name(3)  -> "P3M"
            month_period_name(18) -> "P1Y6M"
    """
    return "".join(append_month_elems(["P"], months))
