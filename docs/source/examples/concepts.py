"""Examples for the "Concepts" page."""

from datetime import datetime

from isoperiod import Period


def origins() -> None:
    """Count 7-day intervals from a chosen start date."""
    # [start:origins]
    p7d = Period.of("2024-01-01/P7D")  # 7-day intervals, counted from 1 Jan 2024

    print(p7d.ordinal(datetime(2024, 1, 1)))
    print(p7d.datetime(1))
    print(p7d.datetime(-1))
    # [end:origins]


def alignment() -> None:
    """Check whether a timestamp sits exactly on a boundary."""
    # [start:alignment]
    pt1h = Period.of_hours(1)

    pt1h.is_aligned(datetime(2024, 3, 1, 9, 0))  # True
    pt1h.is_aligned(datetime(2024, 3, 1, 9, 47))  # False
    # [end:alignment]


def epoch_agnosticism() -> None:
    """Show which periods split the timeline the same way wherever counting begins."""
    # [start:epoch_agnosticism]
    Period.of_days(1).is_epoch_agnostic()  # True
    Period.of_minutes(15).is_epoch_agnostic()  # True
    Period.of_days(7).is_epoch_agnostic()  # False - which 7 days?
    # [end:epoch_agnosticism]
