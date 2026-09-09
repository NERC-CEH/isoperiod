"""Tests for the invariants that must hold for every Period, whatever its step, offset or timezone.

These assert relationships that are true of every period - that str() round-trips, that ordinal() and datetime()
invert each other, that a datetime falls inside the interval it is assigned.  Checks them across a spread of periods
built by combining every step with every kind of offset and timezone.
"""

import datetime

import pytest

from isoperiod import Period

_DURATIONS = [
    "P1Y",
    "P5Y",
    "P1M",
    "P3M",
    "P1D",
    "P7D",
    "PT1H",
    "PT6H",
    "PT1M",
    "PT15M",
    "PT30S",
    "PT0.5S",
    "PT0.04S",
    "PT0.000001S",
]
_OFFSETS = ["", "+9M", "+T9H", "+T5M", "+T0.5S"]
_TZS = [None, datetime.UTC, datetime.timezone(datetime.timedelta(hours=5, minutes=30))]


def _dates_to_test(period: Period) -> list[datetime.datetime]:
    """Datetimes to check `period` at: the ends of its representable range, and two mid-timeline moments."""
    # Find the min and max date that work in the package
    lo, hi = period.min_ordinal, period.max_ordinal
    edges = [period.datetime(ordinal) for ordinal in (lo, lo + 1, (lo + hi) // 2, hi - 1)]

    # Some "normal" dates
    mid_dates = [
        datetime.datetime(1970, 10, 14, 9, 30),
        datetime.datetime(2024, 2, 29, 23, 59, 59, 999_999),
    ]
    return edges + [d.replace(tzinfo=period.tzinfo) for d in mid_dates]


def _every_period() -> list[Period]:
    """Every combination of duration, offset and timezone that forms a legal Period."""
    periods = []
    for duration in _DURATIONS:
        for offset in _OFFSETS:
            try:
                period = Period.of(duration + offset)
            except Exception:  # noqa: BLE001 - a month offset is illegal on a second-based period, and so on
                continue
            periods.extend(period.with_tzinfo(tzinfo) for tzinfo in _TZS)
    return periods


_PERIODS = _every_period()
_IDS = [repr(period) for period in _PERIODS]


@pytest.mark.parametrize("period", _PERIODS, ids=_IDS)
class TestEveryPeriod:
    def test_str_round_trips_through_of(self, period: Period) -> None:
        """Test that str() renders a string Period.of() parses back to the same period."""
        assert Period.of(str(period)) == period.with_tzinfo(None)

    def test_ordinal_and_datetime_are_inverses(self, period: Period) -> None:
        """Test that datetime() undoes ordinal(), for every test datetime."""
        for dt in _dates_to_test(period):
            ordinal = period.ordinal(dt)
            assert period.ordinal(period.datetime(ordinal)) == ordinal

    def test_dt_lies_within_the_interval_it_is_given(self, period: Period) -> None:
        """Test that datetime(n) <= dt < datetime(n + 1), the contract ordinal() documents."""
        for dt in _dates_to_test(period):
            ordinal = period.ordinal(dt)
            assert period.datetime(ordinal) <= dt < period.datetime(ordinal + 1)

    def test_floor_is_the_ordinal_datetime_round_trip(self, period: Period) -> None:
        """Test that floor() is exactly datetime(ordinal(d)), the round trip it stands in for."""
        for dt in _dates_to_test(period):
            assert period.floor(dt) == period.datetime(period.ordinal(dt))

    def test_floor_lands_on_a_boundary_and_stays_there(self, period: Period) -> None:
        """Test that a floored datetime is aligned, and that flooring it again changes nothing."""
        for dt in _dates_to_test(period):
            floored = period.floor(dt)
            assert period.is_aligned(floored)
            assert period.floor(floored) == floored

    def test_interval_bounds_the_datetime_it_holds(self, period: Period) -> None:
        """Test the half-open contract start <= dt < end, for every test datetime."""
        for dt in _dates_to_test(period):
            start, end = period.interval(dt)
            assert start <= dt < end

    def test_intervals_meet_exactly(self, period: Period) -> None:
        """Test that one interval ends where the next begins, leaving no gap and no overlap."""
        for dt in _dates_to_test(period):
            start, end = period.interval(dt)
            assert start == period.floor(dt)
            if period.ordinal(dt) < period.max_ordinal - 1:
                assert period.interval(end)[0] == end

    def test_range_yields_exactly_the_intervals_it_spans(self, period: Period) -> None:
        """Test that a window running from one interval start to another yields the starts between them."""
        mid = (period.min_ordinal + period.max_ordinal) // 2
        starts = [period.datetime(mid + i) for i in range(4)]
        assert list(period.range(starts[0], starts[3])) == starts[:3]
        assert list(period.range(starts[0], starts[0])) == []

    def test_a_period_is_never_shorter_than_itself(self, period: Period) -> None:
        """Test that the ordering is irreflexive, whatever the period's step, offset or timezone."""
        assert not (period < period)
        assert not (period > period)
        assert period <= period
        assert period >= period

    def test_interval_starts_are_aligned(self, period: Period) -> None:
        """Test that the first instant of an interval always reports as aligned."""
        for dt in _dates_to_test(period):
            ordinal = period.ordinal(dt)
            assert period.is_aligned(period.datetime(ordinal))

    def test_a_period_contains_itself_exactly_once(self, period: Period) -> None:
        """Test that every period counts as one of itself and is its own subperiod."""
        assert period.count(period) == 1
        assert period.is_subperiod_of(period)

    def test_base_period_drops_the_offset_and_keeps_the_step(self, period: Period) -> None:
        """Test that base_period() clears any offset while leaving the period's length alone."""
        base = period.base_period()
        assert not base.has_offset()
        assert base.timedelta == period.timedelta

    def test_iso_duration_parses_back_to_the_base_period(self, period: Period) -> None:
        """Test that the iso_duration string describes the period stripped of its offset."""
        assert Period.of_iso_duration(period.iso_duration) == period.base_period().with_tzinfo(None)

    def test_the_representable_range_is_usable_end_to_end(self, period: Period) -> None:
        """Test that both ends of the min_ordinal..max_ordinal range convert to a datetime and back."""
        for ordinal in (period.min_ordinal, period.max_ordinal):
            assert period.ordinal(period.datetime(ordinal)) == ordinal

    def test_stepping_beyond_the_representable_range_raises(self, period: Period) -> None:
        """Test that going past either end of the range raises rather than wrapping or returning nonsense."""
        with pytest.raises((ValueError, OverflowError)):
            period.datetime(period.max_ordinal + 1)
        with pytest.raises((ValueError, OverflowError)):
            period.datetime(period.min_ordinal - 1)

    def test_verbose_and_descriptive_are_never_empty(self, period: Period) -> None:
        """Test that both string forms produce something, for every step, offset and timezone."""
        assert period.verbose
        assert period.descriptive
