"""Examples for the "Interoperability" user guide page.

The Polars example needs ``polars``, which is a documentation dependency of isoperiod rather than a runtime one.
"""

from datetime import UTC, datetime, timedelta

from isoperiod import Period


def string_forms() -> None:
    """Show the three string forms a period offers, and what each is for."""
    # [start:string_forms]
    water_day = Period.of("P1D+T9H")

    print(water_day.iso_duration)  # strict ISO 8601 - the duration alone
    print(str(water_day))  # round-trips through Period.of()
    print(repr(water_day))  # as str(), plus the timezone when there is one
    # [end:string_forms]


def origin_round_trip() -> None:
    """Show that a period with an origin renders in a form that parses back."""
    # [start:origin_round_trip]
    p7d = Period.of("2024-01-01/P7D")

    print(p7d)
    print(Period.of(str(p7d)) == p7d)
    # [end:origin_round_trip]


def repr_adds_the_timezone() -> None:
    """Show the one thing repr adds over str."""
    # [start:repr_adds_the_timezone]

    print(repr(Period.of("PT15M").with_tzinfo(UTC)))
    print(repr(Period.of("PT15M")))
    # [end:repr_adds_the_timezone]


def to_timedelta() -> None:
    """Convert a fixed-length period to a timedelta, and see what calendar periods give."""
    # [start:to_timedelta]
    print(Period.of_minutes(15).timedelta)
    print(Period.of_days(1).timedelta)
    print(Period.of("PT0.04S").timedelta == timedelta(microseconds=40_000))

    print(Period.of_months(1).timedelta)  # no fixed length, so None
    print(Period.of_years(1).timedelta)
    # [end:to_timedelta]


def polars_duration_strings() -> None:
    """Show the Polars duration strings a period emits."""
    # [start:polars_duration_strings]
    print(Period.of_minutes(15).pl_interval)
    print(Period.of_months(1).pl_interval)
    print(Period.of("PT0.04S").pl_interval)

    print(Period.of("P1D+T9H").pl_offset)
    print(Period.of("P1Y+9M").pl_offset)
    # [end:polars_duration_strings]


def polars_group_by_dynamic() -> None:
    """Drive a Polars grouping with a period, aggregating hourly flow into hydrological days."""
    # [start:polars_group_by_dynamic]
    import polars as pl

    water_day = Period.of("P1D+T9H")

    df = pl.DataFrame(
        {
            "timestamp": pl.datetime_range(datetime(2024, 3, 1), datetime(2024, 3, 4), interval="1h", eager=True),
            "flow": range(73),
        }
    )

    daily = (
        df.sort("timestamp")
        .group_by_dynamic("timestamp", every=water_day.pl_interval, offset=water_day.pl_offset)
        .agg(pl.col("flow").mean().alias("mean_flow"), pl.len().alias("n"))
    )

    print(daily)
    # [end:polars_group_by_dynamic]
