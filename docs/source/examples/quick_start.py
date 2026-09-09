"""Examples for the "Quick start" page."""

from datetime import datetime

from isoperiod import Period


def build_a_period() -> None:
    """Build periods from a duration string and from a named unit."""
    # [start:build_a_period]
    pt15m = Period.of("PT15M")
    p1d = Period.of_days(1)
    p1m = Period.of_months(1)
    # [end:build_a_period]
    del pt15m, p1d, p1m


def equal_periods() -> None:
    """Show that periods describing the same grid are equal, however they are spelled."""
    # [start:equal_periods]
    assert Period.of_hours(24) == Period.of_days(1)  # True
    assert Period.of_months(12) == Period.of_years(1)  # True
    # [end:equal_periods]


def find_the_interval() -> None:
    """Map a timestamp to its interval number, and back to the interval's bounds."""
    # [start:find_the_interval]
    pt15m = Period.of("PT15M")
    reading = datetime(2024, 3, 15, 9, 47, 30)

    n = pt15m.ordinal(reading)
    print(pt15m.datetime(n))  # this interval
    print(pt15m.datetime(n + 1))  # the next one
    # [end:find_the_interval]


def flooring() -> None:
    """Snap a timestamp to its interval start in one call."""
    pt15m = Period.of("PT15M")
    reading = datetime(2024, 3, 15, 9, 47, 30)
    # [start:flooring]
    print(pt15m.floor(reading))
    # [end:flooring]


def interval() -> None:
    """Show that the same operations work for calendar units."""
    pt15m = Period.of("PT15M")
    reading = datetime(2024, 3, 15, 9, 47, 30)
    # [start:interval]
    start, end = pt15m.interval(reading)
    print(start, "->", end)
    # [end:interval]


def check_alignment() -> None:
    """Ask whether a timestamp sits exactly on an interval boundary."""
    # [start:check_alignment]
    Period.of_hours(1).is_aligned(datetime(2024, 3, 15, 9, 0))  # True
    Period.of_hours(1).is_aligned(datetime(2024, 3, 15, 9, 47))  # False
    # [end:check_alignment]


def use_an_offset() -> None:
    """Express a hydrological day, running 09:00 to 09:00."""
    # [start:use_an_offset]
    water_day = Period.of_days(1).with_hour_offset(9)

    # 07:30 belongs to the water day that began at 09:00 the previous day.
    print(water_day.floor(datetime(2024, 3, 15, 7, 30)))
    # [end:use_an_offset]


def compare_periods() -> None:
    """Ask how one period nests inside another."""
    # [start:compare_periods]
    pt15m = Period.of("PT15M")
    pt1h = Period.of_hours(1)
    p1d = Period.of_days(1)

    # How many of one period fits inside another
    print(pt15m.count(pt1h))
    print(pt15m.count(p1d))
    # [end:compare_periods]
