"""Examples for the "Describing a period" user guide page."""

from datetime import datetime

from isoperiod import Period


def verbose_and_descriptive() -> None:
    """Show the two properties."""
    # [start:verbose_and_descriptive]
    p1y = Period.of_years(1)

    print("__str__    : ", p1y)
    print("Verbose    : ", p1y.verbose)
    print("Descriptive: ", p1y.descriptive)
    # [end:verbose_and_descriptive]


def frequency_words() -> None:
    """Show a period with a common frequency word, and one that falls back to the plain duration."""
    # [start:frequency_words]
    print(Period.of_days(1).descriptive)
    print(Period.of_months(3).descriptive)
    print(Period.of_seconds(1).descriptive)
    print(Period.of_minutes(15).descriptive)
    # [end:frequency_words]


def named_periods() -> None:
    """Recognised grids get a name, alongside their frequency word."""
    # [start:named_periods]
    water_day = Period.of("P1D+T9H")
    water_year = Period.of("P1Y+9MT9H")

    print(water_day.descriptive)
    print(water_year.descriptive)
    # [end:named_periods]


def offset_and_origin() -> None:
    """An offset appears in brackets; an origin replaces it, since it subsumes the offset."""
    # [start:offset_and_origin]
    water_day = Period.of("P1D+T9H")
    from_a_date = Period.of_days(7).with_origin(datetime(2024, 1, 1))

    print(water_day.verbose)
    print(from_a_date.verbose)
    # [end:offset_and_origin]
