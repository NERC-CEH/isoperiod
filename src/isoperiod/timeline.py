"""Datetime <-> integer timeline arithmetic."""

import calendar
import datetime as dt


def naive(datetime_obj: dt.datetime) -> dt.datetime:
    """Return a datetime object without a tzinfo

    Args:
        datetime_obj: The input datetime object

    Returns:
        A datetime object where tzinfo is None
    """
    return datetime_obj.replace(tzinfo=None)


def total_microseconds(delta: dt.timedelta) -> int:
    """Return total number of microseconds in a timedelta

    Args:
        delta: A datetime timedelta object

    Returns:
        The total number of microseconds in a timedelta
    """
    return delta // dt.timedelta(microseconds=1)


def gregorian_seconds(datetime_obj: dt.datetime) -> int:
    """Calculate number of seconds since the "day epoch"

    The "day epoch" is midnight on day "0" of the proleptic Gregorian ordinal (i.e. midnight at the start of the day
    before January 1 of year 1).

    Args:
        datetime_obj: The input datetime object

    Returns:
        The number of seconds between the supplied datetime and the "day epoch"
    """
    return (datetime_obj.toordinal() * 86_400) + (
        (datetime_obj.hour * 60 + datetime_obj.minute) * 60 + datetime_obj.second
    )


def month_ordinal(date_time: dt.datetime) -> int:
    """Return the number of whole months from the start of year 0 to the start of ``date_time``'s month - the
    "month timeline" position that MonthsPeriod counts in.

    Args:
        date_time: The datetime whose month is wanted

    Returns:
        The month ordinal, e.g. ``datetime(2024, 3, 1)`` -> ``2024 * 12 + 2``
    """
    return date_time.year * 12 + date_time.month - 1


def year_month(ordinal: int) -> tuple[int, int]:
    """Inverse of `month_ordinal`: split a month ordinal back into a (year, month) pair.

    Args:
        ordinal: The month ordinal

    Returns:
        A (year, month) tuple, with month in the usual 1-12 range
    """
    year, month0 = divmod(ordinal, 12)
    return year, month0 + 1


def month_shift(date_time: dt.datetime, shift_amount: int) -> dt.datetime:
    """Shift a datetime object by a given number of months (+ve or -ve)

    Args:
        date_time: The date_time object to be shifted
        shift_amount: The number of months by which to shift date_time

    Returns:
        A datetime object
    """
    if shift_amount == 0:
        return date_time
    new_year, new_month = year_month(month_ordinal(date_time) + shift_amount)
    if date_time.day <= 28:
        return date_time.replace(year=new_year, month=new_month)
    days_in_month = calendar.monthrange(new_year, new_month)[1]
    return date_time.replace(year=new_year, month=new_month, day=min(date_time.day, days_in_month))


def advance(datetime_obj: dt.datetime, month_offset: int, microsecond_offset: int) -> dt.datetime:
    """Move a datetime forward by a month offset and a microsecond offset.

    The month shift is applied first, then the microsecond shift. `retreat` must undo them in the opposite order to
    land back where it started; see `retreat`.

    Args:
        datetime_obj: The datetime object to be shifted
        month_offset: The number of months to shift by
        microsecond_offset: The number of microseconds to shift by

    Returns:
        A datetime object
    """
    return month_shift(datetime_obj, month_offset) + dt.timedelta(microseconds=microsecond_offset)


def retreat(datetime_obj: dt.datetime, month_offset: int, microsecond_offset: int) -> dt.datetime:
    """Move a datetime backward by a month offset and a microsecond offset.

    The month microsecond is applied first, then the month shift. `advance` must undo them in the opposite order to
    land back where it started; see `advance`.

    Args:
        datetime_obj: The datetime object to be shifted
        month_offset: The number of months to shift back by
        microsecond_offset: The number of microseconds to shift back by

    Returns:
        A datetime object
    """
    return month_shift(datetime_obj - dt.timedelta(microseconds=microsecond_offset), 0 - month_offset)
