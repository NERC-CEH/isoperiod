"""Examples for the "Offsets and origins" user guide page."""

from datetime import datetime

from isoperiod import Period


def hydrological_day() -> None:
    """Measure a day from 09:00 to 09:00, as UK hydrological convention does."""
    # [start:hydrological_day]
    water_day = Period.of_days(1).with_hour_offset(9)

    # A reading at 07:30 belongs to the water day that began at 09:00 the previous day.
    print(water_day.floor(datetime(2024, 3, 15, 7, 30)))

    # A reading at 10:00 belongs to the one that began this morning.
    print(water_day.floor(datetime(2024, 3, 15, 10, 0)))
    # [end:hydrological_day]


def hydrological_day_alignment() -> None:
    """Show that alignment follows the shifted boundaries."""
    # [start:hydrological_day_alignment]
    water_day = Period.of("P1D+T9H")

    water_day.is_aligned(datetime(2024, 3, 15, 9, 0))  # True - the water day starts here
    water_day.is_aligned(datetime(2024, 3, 15, 0, 0))  # False - midnight starts nothing now
    # [end:hydrological_day_alignment]


def water_year() -> None:
    """Run a year from 09:00 on 1 October, offset by nine months and nine hours."""
    # [start:water_year]
    water_year = Period.of("P1Y+9MT9H")

    print(water_year.floor(datetime(2024, 3, 15)))
    print(water_year.floor(datetime(2024, 11, 15)))
    # [end:water_year]


def offsets_when_comparing() -> None:
    """Show that offsets are accounted for when periods are compared."""
    # [start:offsets_when_comparing]
    water_year = Period.of("P1Y+9MT9H")

    Period.of("P1D+T9H").is_subperiod_of(water_year)  # True - a water day nests cleanly
    Period.of_days(1).is_subperiod_of(water_year)  # False - straddles every 1 October

    Period.of_hours(1).count(Period.of("P1D+T9H"))  # 24 - hours still fit a 09:00 day
    Period.of_hours(1).is_subperiod_of(Period.of("P1D+T9H30M"))  # False - the half hour breaks it
    # [end:offsets_when_comparing]


def inspecting_an_offset() -> None:
    """Read back the parts of a period that carries an offset."""
    # [start:inspecting_an_offset]
    water_day = Period.of("P1D+T9H")

    print(water_day.has_offset())
    print(water_day.month_offset, water_day.microsecond_offset)
    print(water_day.offset)
    print(water_day.iso_duration)  # the duration alone, without the offset
    print(water_day)  # duration and offset together
    # [end:inspecting_an_offset]


def setting_an_origin() -> None:
    """Make a chosen datetime ordinal 0 and an interval boundary."""
    # [start:setting_an_origin]
    p7d = Period.of_days(7).with_origin(datetime(2024, 1, 1))

    print(p7d.ordinal(datetime(2024, 1, 1)))
    print(p7d.is_aligned(datetime(2024, 1, 1)))
    print(p7d.datetime(1))
    print(p7d.datetime(-1))
    # [end:setting_an_origin]


def origin_from_a_string() -> None:
    """Show that the "<start>/<duration>" string does the same thing as with_origin()."""
    # [start:origin_from_a_string]
    from_string = Period.of("2024-01-01/P7D")
    from_builder = Period.of_days(7).with_origin(datetime(2024, 1, 1))

    print(from_string == from_builder)
    print(from_string)
    # [end:origin_from_a_string]


def removing_offsets_and_origins() -> None:
    """Strip the offset, the numbering, or both."""
    # [start:removing_offsets_and_origins]
    p7d = Period.of("2024-01-01/P7D")

    print(p7d.base_period())
    print(Period.of("P1D+T9H").base_period())

    # The boundaries are unchanged; only the numbering is.
    p7d_no_shift = p7d.without_ordinal_shift()
    print(p7d_no_shift.is_aligned(datetime(2024, 1, 1)))
    print(p7d_no_shift.ordinal(datetime(2024, 1, 1)))
    # [end:removing_offsets_and_origins]
