"""Examples for the "Intervals and ordinals" user guide page."""

from datetime import datetime

from isoperiod import Period


def ordinal_and_datetime() -> None:
    """Map a datetime to its interval number and back."""
    # [start:ordinal_and_datetime]
    pt1h = Period.of_hours(1)
    d = datetime(2024, 3, 1, 9, 47)

    n = pt1h.ordinal(d)  # datetime -> interval number
    print(pt1h.datetime(n))  # interval number -> first instant
    # [end:ordinal_and_datetime]


def flooring() -> None:
    """Snap a timestamp down onto the grid of several periods."""
    # [start:flooring]
    d = datetime(2024, 3, 15, 9, 47, 30)

    print(Period.of_minutes(15).floor(d))
    print(Period.of_days(1).floor(d))
    print(Period.of_months(1).floor(d))
    print(Period.of_years(1).floor(d))
    # [end:flooring]


def flooring_with_offset() -> None:
    """Show that an offset moves what a timestamp floors to."""
    # [start:flooring_with_offset]
    water_day = Period.of("P1D+T9H")

    print(water_day.floor(datetime(2024, 3, 15, 7, 30)))
    # [end:flooring_with_offset]


def stepping() -> None:
    """Walk a monthly grid by adding to an ordinal."""
    # [start:stepping]
    p1m = Period.of_months(1)
    n = p1m.ordinal(datetime(2024, 1, 31))

    for i in range(4):
        print(p1m.datetime(n + i))
    # [end:stepping]


def walking_a_window() -> None:
    """Yield the start of every interval in a window that sits on the boundaries."""
    # [start:walking_a_window]
    pt6h = Period.of_hours(6)

    window_start = datetime(2024, 3, 1)
    window_end = datetime(2024, 3, 2)

    for start in pt6h.range(window_start, window_end):
        print(start)
    # [end:walking_a_window]


def walking_a_partial_window() -> None:
    """Show that a window opening mid-interval still yields the whole of that interval."""
    # [start:walking_a_partial_window]
    pt6h = Period.of_hours(6)

    window_start = datetime(2024, 3, 1, 3)
    window_end = datetime(2024, 3, 1, 13)

    for start in pt6h.range(window_start, window_end):
        print(start)
    # [end:walking_a_partial_window]


def bounding_an_interval() -> None:
    """Get the half-open bounds of the interval holding a datetime."""
    # [start:bounding_an_interval]
    pt1h = Period.of_hours(1)

    start, end = pt1h.interval(datetime(2024, 3, 15, 9, 47))

    print(start, "->", end)
    # [end:bounding_an_interval]


def walking_bounded_intervals() -> None:
    """Combine range() and interval() to walk a window as bounded intervals."""
    # [start:walking_bounded_intervals]
    pt6h = Period.of_hours(6)

    window_start = datetime(2024, 3, 1)
    window_end = datetime(2024, 3, 1, 13)

    for s in pt6h.range(window_start, window_end):
        start, end = pt6h.interval(s)
        print(start, "->", end)
    # [end:walking_bounded_intervals]


def grouping() -> None:
    """Group readings by the interval they fall in, using the ordinal as the key."""
    # [start:grouping]
    readings = {
        datetime(2024, 3, 15, 9, 47): 1.2,
        datetime(2024, 3, 15, 9, 52): 1.4,
        datetime(2024, 3, 15, 10, 3): 1.1,
    }

    pt1h = Period.of_hours(1)

    hourly: dict[datetime, list[float]] = {}
    for when, value in readings.items():
        hourly.setdefault(pt1h.floor(when), []).append(value)

    for hour, values in hourly.items():
        print(hour, values)
    # [end:grouping]


def alignment() -> None:
    """Test whether a datetime sits exactly on an interval boundary."""
    # [start:alignment]
    pt15m = Period.of_minutes(15)

    pt15m.is_aligned(datetime(2024, 3, 15, 9, 45))  # True - on a boundary
    pt15m.is_aligned(datetime(2024, 3, 15, 9, 47))  # False - part-way through an interval
    # [end:alignment]


def alignment_with_offset() -> None:
    """Show that an offset moves what counts as aligned."""
    # [start:alignment_with_offset]
    water_day = Period.of("P1D+T9H")

    water_day.is_aligned(datetime(2024, 3, 15, 9, 0))  # True - the water day starts at 09:00
    water_day.is_aligned(datetime(2024, 3, 15, 0, 0))  # False - midnight no longer starts anything
    # [end:alignment_with_offset]


def what_an_ordinal_is() -> None:
    """Show the familiar quantities that ordinals turn out to be."""
    # [start:what_an_ordinal_is]
    print(Period.of_years(1).ordinal(datetime(2024, 7, 1)))  # the year
    print(Period.of_months(1).ordinal(datetime(2024, 3, 1)))  # months since year 0
    print(Period.of_days(1).ordinal(datetime(2024, 3, 15)))  # the proleptic Gregorian ordinal
    # [end:what_an_ordinal_is]


def ends_of_the_timeline() -> None:
    """Show the usable ordinal range."""
    # [start:ends_of_the_timeline]
    p1y = Period.of_years(1)

    print(p1y.datetime(p1y.min_ordinal))
    print(p1y.datetime(p1y.max_ordinal))
    # [end:ends_of_the_timeline]


def ends_of_the_timeline_error() -> None:
    """Show error on out of bounds."""
    # [start:ends_of_the_timeline_error]
    try:
        Period.of_days(1).datetime(10**9)
    except ValueError as err:
        print(err)
    # [end:ends_of_the_timeline_error]
