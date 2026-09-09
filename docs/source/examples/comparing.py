"""Examples for the "Comparing periods" user guide page."""

from isoperiod import Period


def equality() -> None:
    """Show that periods describing the same grid are equal, however they were built."""
    # [start:equality]
    print(Period.of_hours(24), Period.of_days(1))
    print(Period.of("PT15M"), Period.of_minutes(15), Period.of_seconds(900))
    # [end:equality]


def sorting() -> None:
    """Sort periods shortest first, across calendar and fixed-length alike."""
    # [start:sorting]
    periods = [Period.of_days(100), Period.of("PT1.5S"), Period.of_seconds(1), Period.of_years(1), Period.of_months(1)]

    print(sorted(periods))
    # [end:sorting]


def counting() -> None:
    """Count how many intervals of one period fit inside each interval of another."""
    # [start:counting]
    pt15m = Period.of_minutes(15)
    pt1h = Period.of_hours(1)
    p1d = Period.of_days(1)
    p1m = Period.of_months(1)
    p1y = Period.of_years(1)

    print(pt15m.count(pt1h))
    print(pt1h.count(p1d))
    print(p1m.count(p1y))
    # [end:counting]


def counting_without_an_answer() -> None:
    """Show the two cases that have no constant count, both returning None."""
    # [start:counting_without_an_answer]
    pt1h = Period.of_hours(1)
    p1d = Period.of_days(1)

    print(p1d.count(Period.of_months(1)))  # aligned, but months hold 28-31 days
    print(p1d.count(pt1h))  # the larger never fits inside the smaller
    print(Period.of_minutes(25).count(pt1h))  # 60 is not a multiple of 25
    # [end:counting_without_an_answer]


def counting_with_offsets() -> None:
    """Show that what matters is the difference between offsets, not that they are equal."""
    # [start:counting_with_offsets]
    pt15m_t5m = Period.of("PT15M+T5M")

    print(pt15m_t5m.count(Period.of_hours(1)))  # :05 :20 :35 :50 straddle the hour
    print(pt15m_t5m.count(Period.of("PT1H+T5M")))  # both offset alike
    print(pt15m_t5m.count(Period.of("PT1H+T20M")))  # offsets differ by one 15-minute step
    # [end:counting_with_offsets]


def containment() -> None:
    """Ask whether every interval of one period falls wholly inside one interval of another."""
    # [start:containment]
    pt15m = Period.of_minutes(15)
    pt1h = Period.of_hours(1)
    p1d = Period.of_days(1)

    pt1h.is_subperiod_of(p1d)  # True - an hour never straddles midnight
    p1d.is_subperiod_of(Period.of_months(1))  # True - nor a day a month boundary
    pt15m.is_subperiod_of(pt1h)  # True

    p1d.is_subperiod_of(pt1h)  # False - the larger is never contained by the smaller
    Period.of("PT15M+T5M").is_subperiod_of(pt1h)  # False

    p1d.is_subperiod_of(p1d)  # True - a period always contains itself
    # [end:containment]


def epoch_agnosticism() -> None:
    """Show which periods split the timeline the same way wherever counting begins."""
    # [start:epoch_agnosticism]
    Period.of_minutes(15).is_epoch_agnostic()  # True - 15 minutes divides into a day
    Period.of_hours(6).is_epoch_agnostic()  # True
    Period.of_days(1).is_epoch_agnostic()  # True
    Period.of_months(3).is_epoch_agnostic()  # True - 3 months divides into a year

    Period.of_days(7).is_epoch_agnostic()  # False - which 7 days? depends where you start
    Period.of_minutes(7).is_epoch_agnostic()  # False
    Period.of_months(5).is_epoch_agnostic()  # False
    # [end:epoch_agnosticism]


def an_origin_does_not_change_it() -> None:
    """Show that an origin fixes the numbering, not the way the timeline is split."""
    # [start:an_origin_does_not_change_it]
    p7d = Period.of("2024-01-01/P7D")

    p7d.is_epoch_agnostic()  # False - the same answer as a plain P7D

    # The origin fixes the numbering, not the split: strip it and the plain offset period is left.
    print(p7d.without_ordinal_shift())
    # [end:an_origin_does_not_change_it]
