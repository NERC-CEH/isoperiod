"""Helpers for rendering a period's duration, offset and origin as English words."""

import datetime as dt

from isoperiod.enums import Step
from isoperiod.iso import second_string

_FREQUENCY_WORDS: dict[int, dict[int, str]] = {
    Step.SECONDS: {3_600: "Hourly", 86_400: "Daily", 604_800: "Weekly"},
    Step.MONTHS: {1: "Monthly", 3: "Quarterly", 12: "Yearly"},
}

# Specific periods that this package recognises.
#   Key of dict is: (step, multiplier, month_offset, microsecond_offset)
_NAMED_PERIODS: dict[tuple[int, int, int, int], str] = {
    (Step.SECONDS, 86_400, 0, 32_400_000_000): "UK Water Day",
    (Step.MONTHS, 12, 9, 32_400_000_000): "UK Water Year",
}


def _quantity(amount: str, unit: str) -> str:
    """Return an amount and its unit, pluralised unless the amount is exactly "1".

    Args:
        amount: The rendered amount, e.g. "1" or "0.5"
        unit: The singular unit name, e.g. "day"

    Returns:
        The amount and unit, e.g. "1 day" or "0.5 days"

    Examples:
        >>> _quantity("1", "day")
        '1 day'
        >>> _quantity("0.5", "day")
        '0.5 days'
    """
    return f"{amount} {unit}" if amount == "1" else f"{amount} {unit}s"


def month_words(months: int) -> list[str]:
    """Split a total number of months into year/month word phrases.

    Args:
        months: The total number of months

    Returns:
        A list of "N year(s)" / "N month(s)" phrases, omitting any that are zero

    Examples:
        >>> month_words(18)
        ['1 year', '6 months']
        >>> month_words(3)
        ['3 months']
    """
    years, months_in_year = divmod(months, 12)
    words = []
    if years > 0:
        words.append(_quantity(str(years), "year"))
    if months_in_year > 0 or not words:
        words.append(_quantity(str(months_in_year), "month"))
    return words


def second_words(seconds: int, microseconds: int) -> list[str]:
    """Split a total number of seconds and microseconds into day/hour/minute/second word phrases.

    Args:
        seconds: The total number of whole seconds
        microseconds: The number of microseconds (0-999_999)

    Returns:
        A list of "N day(s)" / "N hour(s)" / "N minute(s)" / "N second(s)" phrases, omitting any that are zero

    Examples:
        >>> second_words(90_061, 0)
        ['1 day', '1 hour', '1 minute', '1 second']
        >>> second_words(0, 500_000)
        ['0.5 seconds']
    """
    days, seconds_in_day = divmod(seconds, 86_400)
    hours, seconds_in_hour = divmod(seconds_in_day, 3_600)
    minutes, seconds_in_minute = divmod(seconds_in_hour, 60)

    words = []
    if days > 0:
        words.append(_quantity(str(days), "day"))
    if hours > 0:
        words.append(_quantity(str(hours), "hour"))
    if minutes > 0:
        words.append(_quantity(str(minutes), "minute"))
    if (seconds_in_minute > 0) or (microseconds > 0) or not words:
        words.append(_quantity(second_string(seconds_in_minute, microseconds), "second"))
    return words


def join_words(words: list[str]) -> str:
    """Join word phrases into an English list, with a comma between each and "and" before the last.

    Args:
        words: The phrases to join

    Returns:
        The joined string

    Examples:
        >>> join_words(["1 day"])
        '1 day'
        >>> join_words(["1 day", "1 hour"])
        '1 day and 1 hour'
        >>> join_words(["1 day", "1 hour", "1 minute"])
        '1 day, 1 hour and 1 minute'
    """
    if len(words) <= 1:
        return "".join(words)
    return f"{', '.join(words[:-1])} and {words[-1]}"


def frequency_word(step: int, multiplier: int) -> str | None:
    """Return the common frequency word for a period's step and multiplier, or None if it has none.

    Args:
        step: The period's step
        multiplier: The period's multiplier

    Returns:
        A word such as "Daily" or "Yearly", or None if this grid has no common name

    Examples:
        >>> frequency_word(Step.SECONDS, 86_400)
        'Daily'
        >>> print(frequency_word(Step.SECONDS, 900))
        None
    """
    return _FREQUENCY_WORDS.get(step, {}).get(multiplier)


def period_name(step: int, multiplier: int, month_offset: int, microsecond_offset: int) -> str | None:
    """Return the recognised name of a period's whole grid, or None if it is not one of them.

    Args:
        step: The period's step
        multiplier: The period's multiplier
        month_offset: The period's month offset
        microsecond_offset: The period's microsecond offset

    Returns:
        A name such as "UK Water Day", or None if this grid is not recognised

    Examples:
        >>> period_name(Step.SECONDS, 86_400, 0, 32_400_000_000)
        'UK Water Day'
        >>> print(period_name(Step.SECONDS, 86_400, 0, 0))
        None
    """
    return _NAMED_PERIODS.get((step, multiplier, month_offset, microsecond_offset))


def origin_text(origin: dt.datetime) -> str:
    """Render a datetime as a date, or a date and time if it does not fall at midnight.

    Args:
        origin: The datetime to render

    Returns:
        A string such as "2024-01-01" or "1883-01-01 09:00"

    Examples:
        >>> origin_text(dt.datetime(2024, 1, 1))
        '2024-01-01'
        >>> origin_text(dt.datetime(1883, 1, 1, 9))
        '1883-01-01 09:00'
    """
    if origin.time() == dt.time.min:
        return origin.date().isoformat()
    if origin.microsecond:
        timespec = "microseconds"
    elif origin.second:
        timespec = "seconds"
    else:
        timespec = "minutes"
    return origin.isoformat(sep=" ", timespec=timespec)
