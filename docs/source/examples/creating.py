"""Examples for the "Creating periods" user guide page."""

from datetime import datetime, timedelta

from isoperiod import Period, PeriodError


def plain_iso_durations() -> None:
    """Build periods from plain ISO 8601 duration strings."""
    # [start:plain_iso_durations]
    p1y = Period.of("P1Y")  # 1 year
    p3m = Period.of("P3M")  # 3 months (a quarter)
    p1d = Period.of("P1D")  # 1 day
    pt15m = Period.of("PT15M")  # 15 minutes
    pt25hz = Period.of("PT0.04S")  # 40 ms - 25 Hz sampling
    # [end:plain_iso_durations]
    del p1y, p3m, p1d, pt15m, pt25hz


def combining_components() -> None:
    """Show that duration components combine, and how the result renders."""
    # [start:combining_components]
    p1y6m = Period.of("P1Y6M")
    p1dt12h = Period.of("P1DT12H")
    pt1h30m = Period.of("PT1H30M")
    # [end:combining_components]
    del p1y6m, p1dt12h, pt1h30m


def offset_form() -> None:
    """Show that the builder methods render as the extended "+offset" string."""
    # [start:offset_form]
    Period.of("P1D+T9H")  # Hydrological day: 09:00am - 09:00am
    Period.of("PT15M+T5M")  # Records measured at :05, :20, :35, :50
    Period.of("P1Y+9MT9H")  # UK Hydrological Year
    # [end:offset_form]


def with_offset_form() -> None:
    """Show that the with offset form is equivalent to the extended "+offset" string."""
    # [start:with_offset_form]
    Period.of("P1D").with_hour_offset(9)  # Hydrological day: 09:00am - 09:00am
    Period.of("PT15M").with_minute_offset(5)  # Records measured at :05, :20, :35, :50
    Period.of("P1Y").with_month_offset(9).with_hour_offset(9)  # UK Hydrological Year
    # [end:with_offset_form]


def origin_form() -> None:
    """Pin the grid to a chosen datetime, which becomes ordinal 0 and a boundary."""
    # [start:origin_form]
    p7d = Period.of("2024-01-01/P7D")

    print(p7d.ordinal(datetime(2024, 1, 1)))
    print(p7d.is_aligned(datetime(2024, 1, 1)))
    print(p7d.datetime(1))
    # [end:origin_form]


def reduced_precision_origin() -> None:
    """Show that a bare year or year-month origin is padded to its first instant."""
    # [start:reduced_precision_origin]
    print(Period.of("2024/P1Y"))
    print(Period.of("2024-10/P1M"))
    print(Period.of("1883-01-01T09:00/P1D"))
    # [end:reduced_precision_origin]


def from_timedelta() -> None:
    """Build a period from any fixed-length timedelta."""
    # [start:from_timedelta]
    print(Period.of_timedelta(timedelta(minutes=30)))
    print(Period.of_timedelta(timedelta(milliseconds=20)))
    print(Period.of_timedelta(timedelta(days=1, hours=12)))
    # [end:from_timedelta]


def handling_bad_input() -> None:
    """Catch PeriodError to cover both the parsing and the validation failure."""

    # [start:handling_bad_input]
    def parse_resolution(text: str) -> Period | None:
        try:
            return Period.of(text)
        except PeriodError as err:
            print(f"{text!r}: {type(err).__name__} - {err}")
            return None

    parse_resolution("PT15M")
    parse_resolution("every 15 mins")  # no supported format matches
    parse_resolution("P1M1D")  # parses, but mixes calendar and clock units
    # [end:handling_bad_input]
