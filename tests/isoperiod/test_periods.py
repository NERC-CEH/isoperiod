import datetime as dt
from collections.abc import Callable

import pytest

from isoperiod import Period
from isoperiod.exceptions import PeriodValidationError
from isoperiod.periods import (
    MonthsPeriod,
    OffsetPeriod,
    SecondsPeriod,
    ShiftedPeriod,
    build_base_period,
    build_offset_period,
)
from isoperiod.properties import Properties

BAD_STEP = 999


def _mutated(base: Properties, **overrides: object) -> Properties:
    """A copy of `base` with fields forced past Properties.__post_init__ validation."""
    clone = Properties(
        step=base.step,
        multiplier=base.multiplier,
        month_offset=base.month_offset,
        microsecond_offset=base.microsecond_offset,
        tzinfo=base.tzinfo,
        ordinal_shift=base.ordinal_shift,
    )
    for name, value in overrides.items():
        object.__setattr__(clone, name, value)
    return clone


class TestUnitConstructors:
    @pytest.mark.parametrize(
        "factory,n,expected_iso",
        [
            (Period.of_years, 1, "P1Y"),
            (Period.of_years, 5, "P5Y"),
            (Period.of_months, 1, "P1M"),
            (Period.of_months, 3, "P3M"),
            (Period.of_months, 12, "P1Y"),
            (Period.of_days, 1, "P1D"),
            (Period.of_days, 7, "P7D"),
            (Period.of_hours, 1, "PT1H"),
            (Period.of_hours, 24, "P1D"),
            (Period.of_minutes, 1, "PT1M"),
            (Period.of_minutes, 15, "PT15M"),
            (Period.of_seconds, 1, "PT1S"),
            (Period.of_seconds, 60, "PT1M"),
            (Period.of_microseconds, 1, "PT0.000001S"),
            (Period.of_microseconds, 1_000_000, "PT1S"),
        ],
        ids=[
            "1 year",
            "5 years",
            "1 month",
            "3 months",
            "12 months -> 1 year",
            "1 day",
            "7 days",
            "1 hour",
            "24 hours -> 1 day",
            "1 minute",
            "15 minutes",
            "1 second",
            "60 seconds -> 1 minute",
            "1 microsecond",
            "1e6 microseconds -> 1 second",
        ],
    )
    def test_builds_expected_duration(self, factory: Callable[[int], Period], n: int, expected_iso: str) -> None:
        """Test that the constructed period's iso_duration matches, including unit normalisation."""
        assert factory(n).iso_duration == expected_iso

    @pytest.mark.parametrize(
        "factory",
        [
            Period.of_years,
            Period.of_months,
            Period.of_days,
            Period.of_hours,
            Period.of_minutes,
            Period.of_seconds,
            Period.of_microseconds,
        ],
        ids=["years", "months", "days", "hours", "minutes", "seconds", "microseconds"],
    )
    @pytest.mark.parametrize("n", [0, -1, -100], ids=["zero", "minus one", "large negative"])
    def test_rejects_non_positive(self, factory: Callable[[int], Period], n: int) -> None:
        """Test that a period of zero or negative length is invalid for every unit."""
        with pytest.raises(PeriodValidationError):
            factory(n)

    @pytest.mark.parametrize(
        "delta,expected_iso",
        [
            (dt.timedelta(days=1), "P1D"),
            (dt.timedelta(hours=1), "PT1H"),
            (dt.timedelta(microseconds=500), "PT0.0005S"),
        ],
        ids=["1 day", "1 hour", "500 microseconds"],
    )
    def test_of_timedelta(self, delta: dt.timedelta, expected_iso: str) -> None:
        """Test that of_timedelta converts a timedelta to the equivalent microsecond-based period."""
        assert Period.of_timedelta(delta).iso_duration == expected_iso

    def test_of_timedelta_rejects_zero(self) -> None:
        """Test that a zero timedelta has no valid period representation."""
        with pytest.raises(PeriodValidationError):
            Period.of_timedelta(dt.timedelta(0))


class TestEquivalentConstructions:
    @pytest.mark.parametrize(
        "a,b",
        [
            (Period.of_years(1), Period.of_months(12)),
            (Period.of_days(1), Period.of_hours(24)),
            (Period.of_hours(1), Period.of_minutes(60)),
            (Period.of_minutes(1), Period.of_seconds(60)),
            (Period.of_seconds(1), Period.of_microseconds(1_000_000)),
            (Period.of("P1D"), Period.of_days(1)),
            (Period.of("p1d"), Period.of_days(1)),
            (Period.of_years(1).with_month_offset(9).with_hour_offset(9), Period.of("P1Y+9MT9H")),
            (Period.of_years(1).with_month_offset(9).with_hour_offset(9), Period.of("p1y+9mt9h")),
        ],
        ids=[
            "1 year == 12 months",
            "1 day == 24 hours",
            "1 hour == 60 minutes",
            "1 minute == 60 seconds",
            "1 second == 1e6 microseconds",
            "of() == of_days()",
            "of() is case-insensitive",
            "with_offset chain == of() extended form",
            "with_offset chain == of() extended form (lowercase)",
        ],
    )
    def test_equivalent(self, a: Period, b: Period) -> None:
        """Test that the two periods compare equal, hash equal, and stringify the same."""
        assert a == b
        assert hash(a) == hash(b)
        assert str(a) == str(b)

    def test_equivalence_class_collapses_to_one_set_member(self) -> None:
        """Test that five construction paths for the water year all collapse to a single set entry."""
        water_year = "P1Y+9MT9H"
        periods = {
            Period.of(water_year),
            Period.of(water_year.upper()),
            Period.of(water_year.lower()),
            Period.of_iso_duration("P1Y").with_month_offset(9).with_hour_offset(9),
            Period.of_years(1).with_month_offset(9).with_hour_offset(9),
        }
        assert len(periods) == 1


class TestStrAndRepr:
    def test_str_is_duration_plus_offset(self) -> None:
        """Test that str() shows the duration and, when present, the '+offset' extension."""
        assert str(Period.of_days(1)) == "P1D"
        assert str(Period.of_days(1).with_hour_offset(9)) == "P1D+T9H"

    def test_repr_includes_timezone(self) -> None:
        """Test that repr() appends the timezone in square brackets."""
        assert repr(Period.of_days(1).with_tzinfo(dt.UTC)) == "P1D[Z]"

    @pytest.mark.parametrize(
        "period",
        [
            Period.of_days(1).with_hour_offset(9),
            Period.of_years(1).with_month_offset(9).with_hour_offset(9),
            Period.of_hours(1),
        ],
        ids=["day + hour offset", "water year", "plain hour"],
    )
    def test_str_round_trips_through_of_duration(self, period: Period) -> None:
        """Test that str(period.without_offset()) + period.offset rebuilds an equal Period."""
        reconstructed = Period.of_duration(str(period.without_offset()) + period.offset)
        assert reconstructed == period


class TestEqualityAndHashing:
    def test_equal_periods_of_different_units(self) -> None:
        """Test that a 1-day period equals a 24-hour period."""
        assert Period.of_days(1) == Period.of_hours(24)

    def test_unequal_periods(self) -> None:
        """Test that different lengths are not equal."""
        assert Period.of_days(1) != Period.of_days(2)

    def test_equal_periods_hash_equal(self) -> None:
        """Test that equal periods hash equal, so they collapse in sets and dict keys."""
        assert hash(Period.of_days(1)) == hash(Period.of_hours(24))

    def test_usable_as_dict_key(self) -> None:
        """Test that a period looked up by an equal period returns the stored value."""
        assert {Period.of_days(1): "daily"}[Period.of_hours(24)] == "daily"

    def test_set_deduplicates_equal_periods(self) -> None:
        """Test that a set of {1 day, 24 hours, 48 hours} has two members."""
        assert len({Period.of_days(1), Period.of_hours(24), Period.of_hours(48)}) == 2

    @pytest.mark.parametrize("other", ["P1D", 1, None, object()], ids=["str", "int", "None", "object"])
    def test_equality_against_non_period_is_false_not_an_error(self, other: object) -> None:
        """Test that comparing to a non-Period returns False instead of raising."""
        assert Period.of_days(1) != other
        assert not (Period.of_days(1) == other)

    @pytest.mark.parametrize("other", ["P1D", 1, None], ids=["str", "int", "None"])
    def test_membership_check_against_non_periods_does_not_raise(self, other: object) -> None:
        """Test that `period in [non_period]` is a plain False (regression: it used to raise)."""
        assert Period.of_days(1) not in [other]


class TestOrdering:
    @pytest.mark.parametrize(
        "smaller,larger",
        [
            (Period.of_minutes(1), Period.of_hours(1)),
            (Period.of_minutes(1), Period.of_minutes(1)),
            (Period.of_hours(1), Period.of_hours(1)),
        ],
        ids=["strictly less", "equal (<=)", "equal (>=)"],
    )
    def test_relative_ordering(self, smaller: Period, larger: Period) -> None:
        """Test that <=, <, >, >= are consistent with the periods' relative size."""
        assert smaller <= larger
        assert larger >= smaller
        assert (smaller < larger) == (smaller != larger)
        assert (larger > smaller) == (smaller != larger)

    def test_sortable_by_size(self) -> None:
        """Test that sorted() orders a mixed list from shortest to longest."""
        periods = [Period.of_days(7), Period.of_hours(1), Period.of_minutes(1)]
        assert sorted(periods) == [Period.of_minutes(1), Period.of_hours(1), Period.of_days(7)]

    @pytest.mark.parametrize(
        "smaller,larger",
        [
            (Period.of("PT1S"), Period.of("PT1.5S")),
            (Period.of("PT1.5S"), Period.of("PT2S")),
            (Period.of("PT0.5S"), Period.of("PT1S")),
            (Period.of_days(1), Period.of_months(1)),
            (Period.of_months(1), Period.of_days(100)),
            (Period.of_days(100), Period.of_years(1)),
            (Period.of_months(11), Period.of_years(1)),
            (Period.of("PT0.000001S"), Period.of_years(1)),
        ],
        ids=[
            "whole second before fractional",
            "fractional before larger whole",
            "sub-second before whole second",
            "day before month",
            "month before 100 days",
            "100 days before year",
            "11 months before year",
            "microsecond before year",
        ],
    )
    def test_ordering_holds_across_steps(self, smaller: Period, larger: Period) -> None:
        """Test that ordering follows length, not the step/multiplier field order.

        Every pair here crosses a step boundary, where sorting by (step, multiplier) - as a dataclass with
        order=True does - gets the answer backwards.
        """
        assert smaller < larger
        assert larger > smaller
        assert not (larger < smaller)

    def test_sorting_is_by_length_across_calendar_and_fixed_periods(self) -> None:
        """Test that a list mixing sub-second, whole-second and calendar periods sorts shortest first."""
        periods = [Period.of_days(100), Period.of("PT1.5S"), Period.of_seconds(1), Period.of_years(1)]
        assert sorted(periods) == [
            Period.of_seconds(1),
            Period.of("PT1.5S"),
            Period.of_days(100),
            Period.of_years(1),
        ]

    def test_periods_of_equal_length_still_order_totally(self) -> None:
        """Test that periods sharing a nominal length but differing elsewhere still sort deterministically."""
        p1m = Period.of_months(1)
        offset = Period.of_months(1).with_month_offset(0).with_second_offset(1)
        assert sorted([offset, p1m]) == [p1m, offset]
        assert (p1m < offset) != (offset < p1m)

    def test_ordering_a_month_against_its_mean_length_in_seconds_is_total(self) -> None:
        """Test that a month and the fixed period of identical nominal length still compare one way only."""
        p1m = Period.of_months(1)
        mean = Period.of_seconds(2_629_746)
        assert p1m != mean
        assert (p1m < mean) != (mean < p1m)

    def test_mismatched_timezones_raise_rather_than_ordering(self) -> None:
        """Test that two otherwise-identical periods on different clocks refuse to order (as datetimes do)."""
        with pytest.raises(TypeError):
            _ = Period.of_hours(1).with_tzinfo(dt.UTC) < Period.of_hours(1)

    def test_differing_length_orders_without_consulting_the_timezone(self) -> None:
        """Test that a mismatched timezone is only reached as a tie-break, so unequal lengths still sort."""
        assert Period.of_hours(1).with_tzinfo(dt.UTC) < Period.of_days(1)

    @pytest.mark.parametrize("op", ["__lt__", "__le__", "__gt__", "__ge__"], ids=["lt", "le", "gt", "ge"])
    def test_ordering_against_non_period_returns_notimplemented(self, op: str) -> None:
        """Test that each ordering dunder returns NotImplemented for a non-Period operand."""
        assert getattr(Period.of_days(1), op)("not a period") is NotImplemented

    def test_sorting_alongside_a_non_period_raises_type_error(self) -> None:
        """Test that because the dunders return NotImplemented, sorting a mixed list raises."""
        with pytest.raises(TypeError):
            sorted([Period.of_days(1), "not a period"])


class TestFloor:
    @pytest.mark.parametrize(
        "period,expected",
        [
            (Period.of_minutes(15), dt.datetime(2024, 3, 15, 9, 45)),
            (Period.of_hours(1), dt.datetime(2024, 3, 15, 9, 0)),
            (Period.of_days(1), dt.datetime(2024, 3, 15)),
            (Period.of_months(1), dt.datetime(2024, 3, 1)),
            (Period.of_years(1), dt.datetime(2024, 1, 1)),
            (Period.of("PT0.04S"), dt.datetime(2024, 3, 15, 9, 47, 30, 480_000)),
        ],
        ids=["15 min", "hour", "day", "month", "year", "40 ms"],
    )
    def test_floors_to_the_start_of_the_containing_interval(self, period: Period, expected: dt.datetime) -> None:
        """Test that floor() returns the first instant of the interval holding the datetime."""
        assert period.floor(dt.datetime(2024, 3, 15, 9, 47, 30, 500_000)) == expected

    def test_floor_matches_the_ordinal_datetime_round_trip(self) -> None:
        """Test that floor() is exactly datetime(ordinal(d)), for every kind of period."""
        moment = dt.datetime(2024, 3, 15, 9, 47, 30, 500_000)
        for period in (
            Period.of("PT15M"),
            Period.of("P1M"),
            Period.of("P1D+T9H"),
            Period.of("P1Y+9MT9H"),
            Period.of("2024-01-01/P7D"),
        ):
            assert period.floor(moment) == period.datetime(period.ordinal(moment))

    def test_floor_respects_an_offset(self) -> None:
        """Test that an offset period floors to its own shifted boundary, not the natural one."""
        assert Period.of("P1D+T9H").floor(dt.datetime(2024, 3, 15, 7, 30)) == dt.datetime(2024, 3, 14, 9, 0)

    def test_a_boundary_floors_to_itself(self) -> None:
        """Test that flooring an interval start leaves it alone."""
        boundary = dt.datetime(2024, 3, 15, 9, 0)
        assert Period.of_hours(1).floor(boundary) == boundary

    def test_floor_is_idempotent(self) -> None:
        """Test that flooring an already-floored datetime changes nothing."""
        period = Period.of("P1D+T9H")
        once = period.floor(dt.datetime(2024, 3, 15, 7, 30))
        assert period.floor(once) == once

    def test_floored_datetime_is_aligned(self) -> None:
        """Test that floor() always lands on a boundary, which is what is_aligned reports."""
        assert Period.of_minutes(15).is_aligned(Period.of_minutes(15).floor(dt.datetime(2024, 3, 15, 9, 47)))

    def test_floor_carries_the_periods_tzinfo(self) -> None:
        """Test that floor() stamps the period's tzinfo, exactly as datetime() does."""
        period = Period.of_hours(1).with_tzinfo(dt.UTC)
        assert period.floor(dt.datetime(2024, 3, 15, 9, 47)).tzinfo == dt.UTC

    def test_floor_ignores_the_tzinfo_of_its_argument(self) -> None:
        """Test that floor() reads wall-clock fields only, as ordinal() documents."""
        period = Period.of_hours(1)
        naive_dt = dt.datetime(2024, 3, 15, 9, 47)
        assert period.floor(naive_dt) == period.floor(naive_dt.replace(tzinfo=dt.UTC))


class TestInterval:
    def test_returns_the_half_open_bounds_of_the_interval(self) -> None:
        """Test that interval() gives this interval's start and the next one's."""
        assert Period.of_hours(1).interval(dt.datetime(2024, 3, 15, 9, 47)) == (
            dt.datetime(2024, 3, 15, 9),
            dt.datetime(2024, 3, 15, 10),
        )

    def test_bounds_a_calendar_interval(self) -> None:
        """Test that a month's bounds follow the calendar rather than a fixed length."""
        assert Period.of_months(1).interval(dt.datetime(2024, 2, 10)) == (
            dt.datetime(2024, 2, 1),
            dt.datetime(2024, 3, 1),
        )

    def test_end_is_the_start_of_the_next_interval(self) -> None:
        """Test that consecutive intervals meet exactly, leaving no gap and no overlap."""
        p = Period.of("P1D+T9H")
        end = p.interval(dt.datetime(2024, 3, 15))[1]
        assert p.interval(end)[0] == end

    def test_bounds_contain_the_datetime_they_were_derived_from(self) -> None:
        """Test the half-open contract: start <= d < end."""
        moment = dt.datetime(2024, 3, 15, 9, 47, 30)
        for period in (Period.of("PT15M"), Period.of("P1M"), Period.of("P1D+T9H"), Period.of("2024-01-01/P7D")):
            start, end = period.interval(moment)
            assert start <= moment < end

    def test_start_agrees_with_floor(self) -> None:
        """Test that the start bound is the same value floor() returns."""
        moment = dt.datetime(2024, 3, 15, 9, 47, 30)
        period = Period.of("P1D+T9H")
        assert period.interval(moment)[0] == period.floor(moment)

    def test_bounds_carry_the_periods_tzinfo(self) -> None:
        """Test that both bounds are stamped with the period's tzinfo, as datetime() does."""
        period = Period.of_hours(1).with_tzinfo(dt.UTC)
        bounds = period.interval(dt.datetime(2024, 3, 15, 9, 47))
        assert all(bound.tzinfo == dt.UTC for bound in bounds)

    def test_end_beyond_the_representable_range_raises(self) -> None:
        """Test that the last interval on the timeline has no representable end, and says so."""
        period = Period.of_days(1)
        with pytest.raises((ValueError, OverflowError)):
            period.interval(period.datetime(period.max_ordinal))

    def test_ignores_the_tzinfo_of_its_argument(self) -> None:
        """Test that the bounds are read off wall-clock fields only, as ordinal() documents."""
        period = Period.of_hours(6)
        naive_dt = dt.datetime(2024, 3, 15, 9, 47)
        assert period.interval(naive_dt) == period.interval(naive_dt.replace(tzinfo=dt.UTC))


class TestRange:
    def test_yields_every_interval_start_in_the_window(self) -> None:
        """Test the straightforward case, where the window sits on the period's boundaries."""
        assert list(Period.of_hours(6).range(dt.datetime(2024, 3, 1), dt.datetime(2024, 3, 2))) == [
            dt.datetime(2024, 3, 1, 0),
            dt.datetime(2024, 3, 1, 6),
            dt.datetime(2024, 3, 1, 12),
            dt.datetime(2024, 3, 1, 18),
        ]

    def test_includes_the_interval_containing_the_start(self) -> None:
        """Test that a window opening mid-interval still yields that interval, from before the window."""
        assert list(Period.of_hours(6).range(dt.datetime(2024, 3, 1, 3), dt.datetime(2024, 3, 1, 13))) == [
            dt.datetime(2024, 3, 1, 0),
            dt.datetime(2024, 3, 1, 6),
            dt.datetime(2024, 3, 1, 12),
        ]

    def test_excludes_the_interval_starting_exactly_at_the_end(self) -> None:
        """Test that the window is half-open: an interval beginning at `end` is outside it."""
        starts = list(Period.of_hours(6).range(dt.datetime(2024, 3, 1), dt.datetime(2024, 3, 1, 12)))
        assert starts == [dt.datetime(2024, 3, 1, 0), dt.datetime(2024, 3, 1, 6)]

    def test_walks_a_calendar_grid(self) -> None:
        """Test that months need no special handling despite their varying length."""
        assert list(Period.of_months(1).range(dt.datetime(2024, 1, 15), dt.datetime(2024, 4, 1))) == [
            dt.datetime(2024, 1, 1),
            dt.datetime(2024, 2, 1),
            dt.datetime(2024, 3, 1),
        ]

    def test_respects_an_offset(self) -> None:
        """Test that an offset period walks its own shifted boundaries."""
        assert list(Period.of("P1D+T9H").range(dt.datetime(2024, 3, 1), dt.datetime(2024, 3, 3))) == [
            dt.datetime(2024, 2, 29, 9),
            dt.datetime(2024, 3, 1, 9),
            dt.datetime(2024, 3, 2, 9),
        ]

    @pytest.mark.parametrize(
        "start,end",
        [
            (dt.datetime(2024, 3, 1), dt.datetime(2024, 3, 1)),
            (dt.datetime(2024, 3, 2), dt.datetime(2024, 3, 1)),
            (dt.datetime(2024, 3, 1, 5), dt.datetime(2024, 3, 1, 1)),
        ],
        ids=["empty window", "reversed window", "reversed within one interval"],
    )
    def test_a_window_that_does_not_open_yields_nothing(self, start: dt.datetime, end: dt.datetime) -> None:
        """Test that an empty or backwards window yields no intervals rather than one."""
        assert list(Period.of_hours(6).range(start, end)) == []

    def test_a_window_inside_one_interval_yields_that_interval(self) -> None:
        """Test that a window too small to span a boundary still reports the interval it sits in."""
        assert list(Period.of_hours(6).range(dt.datetime(2024, 3, 1, 1), dt.datetime(2024, 3, 1, 2))) == [
            dt.datetime(2024, 3, 1, 0)
        ]

    def test_every_yielded_start_is_aligned(self) -> None:
        """Test that range() only ever yields real interval boundaries."""
        period = Period.of("P1D+T9H")
        assert all(period.is_aligned(s) for s in period.range(dt.datetime(2024, 1, 1), dt.datetime(2024, 2, 1)))

    def test_yielded_starts_are_consecutive_ordinals(self) -> None:
        """Test that the walk skips nothing and repeats nothing."""
        period = Period.of_months(1)
        ordinals = [period.ordinal(s) for s in period.range(dt.datetime(2024, 1, 15), dt.datetime(2025, 1, 1))]
        assert ordinals == list(range(ordinals[0], ordinals[0] + len(ordinals)))

    def test_yields_lazily(self) -> None:
        """Test that a window spanning a huge number of intervals costs nothing until iterated."""
        walk = Period.of("PT0.000001S").range(dt.datetime(1, 1, 1), dt.datetime(9999, 12, 31))
        assert next(walk) == dt.datetime(1, 1, 1)

    def test_ignores_the_tzinfo_of_its_arguments(self) -> None:
        """Test that the window is read as wall-clock, as ordinal() documents."""
        period = Period.of_hours(6)
        start, end = dt.datetime(2024, 3, 1), dt.datetime(2024, 3, 2)
        assert list(period.range(start, end)) == list(
            period.range(start.replace(tzinfo=dt.UTC), end.replace(tzinfo=dt.UTC))
        )

    def test_yielded_starts_carry_the_periods_tzinfo(self) -> None:
        """Test that yielded datetimes are stamped with the period's tzinfo."""
        period = Period.of_hours(6).with_tzinfo(dt.UTC)
        assert all(s.tzinfo == dt.UTC for s in period.range(dt.datetime(2024, 3, 1), dt.datetime(2024, 3, 2)))


class TestScalarProperties:
    def test_iso_duration(self) -> None:
        """Test that iso_duration is the plain ISO 8601 string, without any offset."""
        assert Period.of_days(1).iso_duration == "P1D"

    def test_tzinfo_defaults_to_none(self) -> None:
        """Test that a period built from a unit constructor is naive."""
        assert Period.of_days(1).tzinfo is None

    def test_pl_interval_is_a_polars_duration_string(self) -> None:
        """Test that pl_interval renders the step/multiplier in Polars units."""
        assert Period.of_days(1).pl_interval == "86400s"

    def test_pl_offset_carries_month_and_microsecond_terms(self) -> None:
        """Test that pl_offset always emits both a 'mo' and a 'us' term."""
        p = Period.of_days(1).with_hour_offset(9)
        assert "mo" in p.pl_offset and "us" in p.pl_offset

    def test_offset_string(self) -> None:
        """Test that offset is the '+<offset>' suffix (seconds, not H/M/S units), empty when there is none."""
        assert Period.of_days(1).offset == ""
        assert Period.of_days(1).with_hour_offset(9).offset == "+T32400S"

    @pytest.mark.parametrize(
        "period,expected",
        [
            (Period.of_hours(1), dt.timedelta(hours=1)),
            (Period.of_months(1), None),
            (Period.of_years(1), None),
        ],
        ids=["fixed-length hour", "calendar month", "calendar year"],
    )
    def test_timedelta(self, period: Period, expected: dt.timedelta | None) -> None:
        """Test that timedelta is a value for fixed-length periods and None for calendar ones."""
        assert period.timedelta == expected

    @pytest.mark.parametrize(
        "period,expected",
        [(Period.of_days(1), True), (Period.of_days(7), False)],
        ids=["1 day is agnostic", "7 days is not"],
    )
    def test_is_epoch_agnostic(self, period: Period, expected: bool) -> None:
        """Test that is_epoch_agnostic reports whether the split is independent of the epoch."""
        assert period.is_epoch_agnostic() is expected


class TestOffsetStringSubSecondPrecision:
    def test_offset_property_keeps_sub_second_precision(self) -> None:
        """Test that a half-second offset renders as '+T0.5S'; a regression, as it once truncated to '+T0S'."""
        assert Period.of_seconds(10).with_microsecond_offset(500_000).offset == "+T0.5S"

    @pytest.mark.parametrize(
        "period",
        [
            Period.of_seconds(10).with_microsecond_offset(500_000),
            Period.of_hours(1).with_microsecond_offset(1_500_000),
        ],
        ids=["half second", "1.5 seconds"],
    )
    def test_sub_second_offset_round_trips_through_of_duration(self, period: Period) -> None:
        """Test that str(without_offset) + offset rebuilds an equal Period for sub-second offsets."""
        assert Period.of_duration(str(period.without_offset()) + period.offset) == period


_KNOWN_ORDINALS = [
    (Period.of_years(1), dt.datetime(2024, 1, 1), 2024),
    (Period.of_months(1), dt.datetime(2024, 3, 1), 2024 * 12 + 2),
    (Period.of_years(10), dt.datetime(2024, 1, 1), 202),
    (Period.of_days(1), dt.datetime(5432, 2, 29), 1_983_691),
    (Period.of_hours(1), dt.datetime(2024, 1, 1, 5), 17_733_269),
    (Period.of_minutes(15), dt.datetime(2024, 1, 1, 0, 30), 70_933_058),
]


class TestOrdinal:
    @pytest.mark.parametrize(
        "period,datetime_obj,expected",
        _KNOWN_ORDINALS,
        ids=["1 year", "1 month", "10 years", "1 day (far-future leap year)", "1 hour", "15 minutes"],
    )
    def test_known_values(self, period: Period, datetime_obj: dt.datetime, expected: int) -> None:
        """Test that a representative datetime maps to its exact, pre-computed ordinal."""
        assert period.ordinal(datetime_obj) == expected


class TestOrdinalDatetimeRoundTrip:
    @pytest.mark.parametrize(
        "period",
        [
            Period.of_years(1),
            Period.of_months(1),
            Period.of_months(3),
            Period.of_days(1),
            Period.of_days(7),
            Period.of_hours(1),
            Period.of_hours(6),
            Period.of_minutes(15),
            Period.of_seconds(30),
            Period.of_microseconds(500_000),
            Period.of_days(1).with_tzinfo(dt.UTC),
            Period.of_hours(1).with_tzinfo(dt.timezone(dt.timedelta(hours=5, minutes=30))),
        ],
        ids=["P1Y", "P1M", "P3M", "P1D", "P7D", "PT1H", "PT6H", "PT15M", "PT30S", "PT0.5S", "P1D UTC", "PT1H +05:30"],
    )
    def test_round_trips_across_a_sample_range(self, period: Period) -> None:
        """Test that ordinal(datetime(o)) == o for the endpoints and midpoint of the valid range."""
        lo, hi = period.min_ordinal, period.max_ordinal
        for ordinal in (lo, lo + 1, hi - 1, hi, (lo + hi) // 2):
            assert period.ordinal(period.datetime(ordinal)) == ordinal


class TestMinMaxOrdinal:
    def test_datetime_of_min_ordinal_is_representable(self) -> None:
        """Test that datetime(min_ordinal) does not raise for being out of datetime's range."""
        p = Period.of_days(1)
        assert p.datetime(p.min_ordinal) is not None

    def test_datetime_of_max_ordinal_is_representable(self) -> None:
        """Test that datetime(max_ordinal) does not raise for being out of datetime's range."""
        p = Period.of_days(1)
        assert p.datetime(p.max_ordinal) is not None

    def test_max_ordinal_matches_ordinal_of_datetime_max(self) -> None:
        """Test that max_ordinal equals the ordinal of datetime.max."""
        p = Period.of_days(1)
        assert p.max_ordinal == p.ordinal(dt.datetime.max)

    @pytest.mark.parametrize(
        "period",
        [Period.of_years(1), Period.of_days(1), Period.of_hours(1), Period.of_days(1).with_hour_offset(9)],
        ids=["P1Y", "P1D", "PT1H", "P1D+T9H"],
    )
    def test_datetime_of_min_ordinal_never_raises(self, period: Period) -> None:
        """Test that the min_ordinal guard holds for offset periods too."""
        period.datetime(period.min_ordinal)


class TestIsAligned:
    @pytest.mark.parametrize(
        "period,datetime_obj",
        [
            (Period.of_days(1), dt.datetime(2024, 1, 1)),
            (Period.of_hours(1), dt.datetime(2024, 1, 1, 5, 0, 0)),
            (Period.of_minutes(15), dt.datetime(2024, 1, 1, 0, 15)),
        ],
        ids=["day boundary", "hour boundary", "quarter-hour boundary"],
    )
    def test_aligned(self, period: Period, datetime_obj: dt.datetime) -> None:
        """Test that a datetime on a boundary is aligned."""
        assert period.is_aligned(datetime_obj)

    @pytest.mark.parametrize(
        "period,datetime_obj",
        [
            (Period.of_days(1), dt.datetime(2024, 1, 1, 0, 0, 1)),
            (Period.of_hours(1), dt.datetime(2024, 1, 1, 5, 30)),
            (Period.of_minutes(15), dt.datetime(2024, 1, 1, 0, 5)),
        ],
        ids=["1s past midnight", "half past the hour", "5 past the quarter"],
    )
    def test_not_aligned(self, period: Period, datetime_obj: dt.datetime) -> None:
        """Test that a datetime inside an interval is not aligned."""
        assert not period.is_aligned(datetime_obj)

    def test_offset_period_alignment_follows_the_offset(self) -> None:
        """Test that a day period offset to 09:00 is aligned at 09:00, not at midnight."""
        water_day = Period.of_days(1).with_hour_offset(9)
        assert water_day.is_aligned(dt.datetime(2024, 1, 1, 9, 0, 0))
        assert not water_day.is_aligned(dt.datetime(2024, 1, 1, 0, 0, 0))

    def test_with_origin_is_aligned_at_its_origin(self) -> None:
        """Test that a period given an explicit origin is aligned (and ordinal 0) there."""
        origin = dt.datetime(1457, 3, 6, 9, 8, 1, 123_456)
        p = Period.of_minutes(15).with_origin(origin)
        assert p.ordinal(origin) == 0
        assert p.is_aligned(origin)


class TestCount:
    @pytest.mark.parametrize(
        "inner,outer,expected",
        [
            (Period.of_hours(1), Period.of_days(1), 24),
            (Period.of_seconds(1), Period.of_hours(1), 3_600),
            (Period.of_months(1), Period.of_years(1), 12),
        ],
        ids=["hours in a day", "seconds in an hour", "months in a year"],
    )
    def test_constant_counts(self, inner: Period, outer: Period, expected: int) -> None:
        """Test that a constant nested count is returned as that number."""
        assert inner.count(outer) == expected

    @pytest.mark.parametrize(
        "inner,outer,aligned",
        [
            (Period.of_days(1), Period.of_months(1), True),
            (Period.of_hours(1), Period.of_seconds(1), False),
        ],
        ids=["days in a month (aligned, count varies)", "larger within smaller (unaligned)"],
    )
    def test_no_constant_count_is_none(self, inner: Period, outer: Period, aligned: bool) -> None:
        """Test that both the "aligned but varying" and "unaligned" cases return None, and that
        is_subperiod_of() is what tells them apart."""
        assert inner.count(outer) is None
        assert inner.is_subperiod_of(outer) is aligned

    def test_matching_offsets_still_nest(self) -> None:
        """Test that two periods sharing the same offset nest exactly as their bare forms do."""
        p1h = Period.of_hours(1).with_minute_offset(1)
        p1d = Period.of_days(1).with_minute_offset(1)
        assert p1h.count(p1d) == 24

    def test_mismatched_offset_breaks_alignment(self) -> None:
        """Test that an offset on only one side makes the periods unaligned."""
        inner = Period.of_hours(1).with_minute_offset(1)
        assert inner.count(Period.of_days(1)) is None
        assert not inner.is_subperiod_of(Period.of_days(1))

    def test_offsets_differing_by_a_whole_inner_period_still_align(self) -> None:
        """Test that the offsets need not be equal, only congruent modulo the inner period. A 15-minute period offset by
        5 has boundaries at :05, :20, :35 and :50, so an hourly period starting at :20 is split cleanly by it - its
        interval :20 -> :20 holds exactly four of them."""
        inner = Period.of_minutes(15).with_minute_offset(5)
        outer = Period.of_hours(1).with_minute_offset(20)
        assert inner.count(outer) == 4
        assert inner.is_subperiod_of(outer)

    def test_offsets_differing_by_part_of_the_inner_period_do_not_align(self) -> None:
        """Test that an offset difference that is not a whole inner period leaves the outer period starting part-way
        through one of the inner intervals."""
        inner = Period.of_minutes(15).with_minute_offset(5)
        outer = Period.of_hours(1).with_minute_offset(12)
        assert inner.count(outer) is None
        assert not inner.is_subperiod_of(outer)

    def test_different_timezones_are_unaligned(self) -> None:
        """Test that a naive period and a UTC period never align."""
        aware = Period.of_hours(1).with_tzinfo(dt.UTC)
        assert Period.of_hours(1).count(aware) is None
        assert not Period.of_hours(1).is_subperiod_of(aware)

    def test_a_period_counts_as_one_of_itself(self) -> None:
        """Test that count() of a period with itself is 1, offsets included."""
        p = Period.of_hours(1).with_minute_offset(5)
        assert p.count(p) == 1


class TestIsSubperiodOf:
    @pytest.mark.parametrize(
        "inner,outer",
        [
            (Period.of_hours(1), Period.of_days(1)),
            (Period.of_days(1), Period.of_months(1)),
        ],
        ids=["hour in day", "day in month"],
    )
    def test_true_when_aligned(self, inner: Period, outer: Period) -> None:
        """Test that an aligned inner period is a subperiod of the outer one."""
        assert inner.is_subperiod_of(outer)

    @pytest.mark.parametrize(
        "inner,outer",
        [
            (Period.of_hours(1).with_minute_offset(1), Period.of_days(1)),
            (Period.of_hours(1), Period.of_seconds(1)),
            (Period.of_months(3).with_month_offset(2), Period.of_years(1).with_month_offset(3)),
        ],
        ids=["unaligned offset", "larger within smaller", "mismatched month offsets"],
    )
    def test_false_when_unaligned(self, inner: Period, outer: Period) -> None:
        """Test that an unaligned pair is not in a subperiod relationship."""
        assert not inner.is_subperiod_of(outer)

    def test_period_is_a_subperiod_of_itself(self) -> None:
        """Test that every period is trivially a subperiod of itself."""
        p = Period.of_minutes(5)
        assert p.is_subperiod_of(p)


class TestOffsetBuilders:
    def test_year_offset_is_months(self) -> None:
        """Test that with_year_offset(9) is with_month_offset(108)."""
        assert Period.of_years(1).with_year_offset(9) == Period.of_years(1).with_month_offset(108)

    def test_month_offset_sets_month_offset(self) -> None:
        """Test that with_month_offset stores the value and marks the period as offset."""
        p = Period.of_years(1).with_month_offset(9)
        assert p.month_offset == 9
        assert p.has_offset()

    def test_day_offset_is_hours(self) -> None:
        """Test that with_day_offset(1) is with_hour_offset(24)."""
        assert Period.of_days(7).with_day_offset(1) == Period.of_days(7).with_hour_offset(24)

    def test_hour_offset_sets_microsecond_offset_without_touching_the_duration(self) -> None:
        """Test that with_hour_offset stores microseconds and leaves iso_duration unchanged."""
        p = Period.of_days(1).with_hour_offset(9)
        assert p.microsecond_offset == 9 * 3_600 * 1_000_000
        assert p.iso_duration == "P1D"
        assert str(p) == "P1D+T9H"

    def test_minute_offset_normalises_away_a_full_period(self) -> None:
        """Test that a 60-minute offset on a 1-hour period nets out to no offset."""
        assert Period.of_hours(1).with_minute_offset(60) == Period.of_hours(1)

    def test_second_offset(self) -> None:
        """Test that with_second_offset stores the value in microseconds."""
        assert Period.of_minutes(1).with_second_offset(30).microsecond_offset == 30_000_000

    def test_microsecond_offset(self) -> None:
        """Test that with_microsecond_offset stores the raw microseconds and shows in str()."""
        p = Period.of_seconds(10).with_microsecond_offset(500_000)
        assert p.microsecond_offset == 500_000
        assert str(p) == "PT10S+T0.5S"

    def test_chained_offsets_compose(self) -> None:
        """Test that a month offset and an hour offset combine into the water-year form."""
        assert str(Period.of_years(1).with_month_offset(9).with_hour_offset(9)) == "P1Y+9MT9H"


class TestHasOffset:
    def test_false_without_an_offset(self) -> None:
        """Test that a plain period reports no offset."""
        assert not Period.of_days(1).has_offset()

    @pytest.mark.parametrize(
        "period",
        [Period.of_years(1).with_month_offset(1), Period.of_days(1).with_hour_offset(1)],
        ids=["month offset", "microsecond offset"],
    )
    def test_true_with_an_offset(self, period: Period) -> None:
        """Test that either kind of offset makes has_offset true."""
        assert period.has_offset()


class TestWithTzinfo:
    def test_adds_tzinfo(self) -> None:
        """Test that the timezone is stored on the returned period."""
        assert Period.of_days(1).with_tzinfo(dt.UTC).tzinfo == dt.UTC

    def test_same_value_returns_self(self) -> None:
        """Test that setting the timezone it already has returns the same object."""
        p = Period.of_days(1)
        assert p.with_tzinfo(None) is p

    def test_removes_tzinfo(self) -> None:
        """Test that passing None clears a previously set timezone."""
        assert Period.of_days(1).with_tzinfo(dt.UTC).with_tzinfo(None).tzinfo is None


class TestWithoutOffset:
    def test_removes_the_offset(self) -> None:
        """Test that the result has no offset and equals the plain period."""
        result = Period.of_days(1).with_hour_offset(9).without_offset()
        assert not result.has_offset()
        assert result == Period.of_days(1)

    def test_noop_returns_self(self) -> None:
        """Test that a period with no offset returns itself."""
        p = Period.of_days(1)
        assert p.without_offset() is p


class TestWithoutOrdinalShift:
    def test_removes_shift_keeps_alignment(self) -> None:
        """Test that boundaries are unchanged; only the ordinal numbering differs."""
        origin = dt.datetime(2000, 1, 1, 6)
        p = Period.of_hours(1).with_origin(origin)
        result = p.without_ordinal_shift()
        assert result.is_aligned(origin)
        assert result.ordinal(origin) != p.ordinal(origin) or p.ordinal(origin) == 0

    def test_noop_returns_self(self) -> None:
        """Test that a period with no shift returns itself."""
        p = Period.of_days(1)
        assert p.without_ordinal_shift() is p


class TestWithOrigin:
    def test_ordinal_zero_and_aligned_at_the_origin(self) -> None:
        """Test that the origin datetime maps to ordinal 0 and is aligned."""
        origin = dt.datetime(1457, 3, 6, 9, 8, 1, 123_456)
        p = Period.of_minutes(15).with_origin(origin)
        assert p.ordinal(origin) == 0
        assert p.is_aligned(origin)

    def test_derives_the_offset_string(self) -> None:
        """Test that the origin's sub-period part becomes the offset string."""
        origin = dt.datetime(1457, 3, 6, 9, 8, 1, 123_456)
        assert str(Period.of_minutes(15).with_origin(origin)) == "PT15M+T8M1.123456S"

    def test_month_step_origin_derives_month_and_time_offset(self) -> None:
        """Test that a water-year origin (Oct 1, 09:00) is ordinal 0 and aligned for a yearly period."""
        origin = dt.datetime(2000, 10, 1, 9)
        p = Period.of_years(1).with_origin(origin)
        assert p.ordinal(origin) == 0
        assert p.is_aligned(origin)

    def test_discards_any_previous_offset_and_shift(self) -> None:
        """Test that an earlier offset is replaced, not combined, by the new origin."""
        p = Period.of_days(1).with_hour_offset(3).with_origin(dt.datetime(2000, 1, 1))
        assert p.ordinal(dt.datetime(2000, 1, 1)) == 0


class TestBasePeriod:
    def test_plain_period_is_its_own_base(self) -> None:
        """Test that a period with no offset/shift returns itself."""
        p = Period.of_days(1)
        assert p.base_period() is p

    @pytest.mark.parametrize(
        "period",
        [
            Period.of_days(1).with_hour_offset(9),
            Period.of_days(1).with_hour_offset(9).with_origin(dt.datetime(2000, 1, 1, 9)),
        ],
        ids=["offset period", "shifted offset period"],
    )
    def test_derived_period_base_is_the_plain_period(self, period: Period) -> None:
        """Test that an offset or shifted period's base is the plain 1-day period."""
        assert period.base_period() == Period.of_days(1)


class TestConstructorValidation:
    @pytest.mark.parametrize(
        "overrides",
        [{"step": BAD_STEP}, {"month_offset": -1}, {"microsecond_offset": -1}],
        ids=["bad step", "negative month offset", "negative microsecond offset"],
    )
    def test_properties_rejects_corrupt_field_at_construction(self, overrides: dict[str, object]) -> None:
        """Test that the corrupt values Period used to re-check are refused by Properties itself, so they can never
        reach a Period in the first place."""
        base = Properties.of_seconds(10)
        with pytest.raises(PeriodValidationError):
            Properties(
                step=overrides.get("step", base.step),  # type: ignore[arg-type]
                multiplier=base.multiplier,
                month_offset=overrides.get("month_offset", base.month_offset),  # type: ignore[arg-type]
                microsecond_offset=overrides.get("microsecond_offset", base.microsecond_offset),  # type: ignore[arg-type]
                tzinfo=base.tzinfo,
                ordinal_shift=base.ordinal_shift,
            )

    def test_ordinal_shift_is_caught_by_the_subclass_invariant(self) -> None:
        """Test that a base-period subclass still rejects a shift it cannot represent."""
        with pytest.raises(PeriodValidationError):
            SecondsPeriod(_mutated(Properties.of_seconds(10), ordinal_shift=5))


class TestBasePeriodValidation:
    def test_step_must_match_the_subclass(self) -> None:
        """Test that a SECONDS Properties handed to MonthsPeriod is rejected."""
        with pytest.raises(PeriodValidationError):
            MonthsPeriod(Properties.of_seconds(10))

    @pytest.mark.parametrize(
        "overrides",
        [{"month_offset": 5}, {"microsecond_offset": 5}, {"ordinal_shift": 5}],
        ids=["month offset", "microsecond offset", "ordinal shift"],
    )
    def test_offset_or_shift_is_rejected(self, overrides: dict[str, object]) -> None:
        """Test that a base-period subclass rejects any offset or ordinal shift."""
        with pytest.raises(PeriodValidationError):
            SecondsPeriod(_mutated(Properties.of_seconds(10), **overrides))


class TestBuilderGuards:
    def test_build_offset_period_rejects_an_ordinal_shift(self) -> None:
        """Test that build_offset_period is for offsets only; a shift must go through build_shifted_period."""
        with pytest.raises(PeriodValidationError):
            build_offset_period(_mutated(Properties.of_seconds(10), microsecond_offset=5_000_000, ordinal_shift=5))

    @pytest.mark.parametrize(
        "overrides",
        [{"month_offset": 5}, {"microsecond_offset": 5}, {"step": BAD_STEP}],
        ids=["month offset", "microsecond offset", "bad step"],
    )
    def test_build_base_period_rejects_offsets_and_bad_steps(self, overrides: dict[str, object]) -> None:
        """Test that build_base_period only accepts a plain, valid-step Properties."""
        with pytest.raises(PeriodValidationError):
            build_base_period(_mutated(Properties.of_seconds(10), **overrides))


class TestOffsetAndShiftedPeriodGuards:
    def test_offset_period_requires_an_offset(self) -> None:
        """Test that constructing OffsetPeriod without an offset raises."""
        with pytest.raises(PeriodValidationError):
            OffsetPeriod(Properties.of_seconds(10))

    def test_offset_period_rejects_an_ordinal_shift(self) -> None:
        """Test that an OffsetPeriod must not also carry a shift."""
        with pytest.raises(PeriodValidationError):
            OffsetPeriod(_mutated(Properties.of_seconds(10), microsecond_offset=5_000_000, ordinal_shift=5))

    def test_shifted_period_requires_a_shift(self) -> None:
        """Test that constructing ShiftedPeriod with a zero shift raises."""
        with pytest.raises(PeriodValidationError):
            ShiftedPeriod(Properties.of_seconds(10))
