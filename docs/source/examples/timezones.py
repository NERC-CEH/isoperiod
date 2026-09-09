"""Examples for the "Time zones" user guide page."""

from datetime import UTC, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from isoperiod import Period

IST = timezone(timedelta(hours=5, minutes=30))


def stamping_returned_datetimes() -> None:
    """Show that datetime() attaches the period's tzinfo to what it returns."""
    # [start:stamping_returned_datetimes]
    pt1h_utc = Period.of_hours(1).with_tzinfo(UTC)

    print(pt1h_utc.tzinfo)
    print(pt1h_utc.floor(datetime(2024, 3, 1, 9, 30)))
    # [end:stamping_returned_datetimes]


def input_tzinfo_is_ignored() -> None:
    """Show that the tzinfo on an incoming datetime is not applied."""
    # [start:input_tzinfo_is_ignored]
    pt1h_utc = Period.of_hours(1).with_tzinfo(UTC)
    d = datetime(2024, 3, 1, 9, 30)

    # The same wall-clock time lands in the same interval, whatever tzinfo it claims.
    print(pt1h_utc.ordinal(d))
    print(pt1h_utc.ordinal(d.replace(tzinfo=UTC)))
    print(pt1h_utc.ordinal(d.replace(tzinfo=IST)))
    # [end:input_tzinfo_is_ignored]


def periods_on_different_clocks_are_distinct() -> None:
    """Show that a period at UTC is not equal to a naive one."""
    # [start:periods_on_different_clocks_are_distinct]
    without_tz = Period.of_hours(1)
    with_tz = Period.of_hours(1).with_tzinfo(UTC)

    print(repr(without_tz))
    print(repr(with_tz))

    print(without_tz == with_tz)
    # [end:periods_on_different_clocks_are_distinct]


def showing_the_timezone() -> None:
    """Show how repr renders a named zone, a fixed offset, and a naive period."""
    # [start:showing_the_timezone]
    print(repr(Period.of_hours(1).with_tzinfo(UTC)))
    print(repr(Period.of_hours(1).with_tzinfo(IST)))
    print(repr(Period.of_hours(1).with_tzinfo(ZoneInfo("Europe/London"))))
    print(repr(Period.of_hours(1)))
    # [end:showing_the_timezone]


def convert_before_asking() -> None:
    """Do period arithmetic in UTC, converting local readings first."""
    # [start:convert_before_asking]
    p1d_utc = Period.of_days(1).with_tzinfo(UTC)

    local_reading = datetime(2024, 3, 31, 2, 30, tzinfo=IST)
    utc_reading = local_reading.astimezone(UTC)  # convert first ...

    print(p1d_utc.floor(utc_reading))  # ... then ask the period
    # [end:convert_before_asking]
