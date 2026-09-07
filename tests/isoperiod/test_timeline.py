import datetime as dt

import pytest

from isoperiod.timeline import (
    advance,
    gregorian_seconds,
    month_ordinal,
    month_shift,
    naive,
    retreat,
    total_microseconds,
    year_month,
)


class TestMonthShift:
    def test_zero_shift_returns_the_same_object(self) -> None:
        """Test that a shift of 0 is a no-op and returns the input unchanged."""
        d = dt.datetime(2024, 1, 1)
        assert month_shift(d, 0) is d

    @pytest.mark.parametrize(
        "start,months,expected",
        [
            (dt.datetime(2024, 1, 15), 1, dt.datetime(2024, 2, 15)),
            (dt.datetime(2024, 3, 15), -1, dt.datetime(2024, 2, 15)),
            (dt.datetime(2023, 12, 1), 1, dt.datetime(2024, 1, 1)),
            (dt.datetime(2024, 1, 1), -1, dt.datetime(2023, 12, 1)),
            (dt.datetime(2020, 1, 1), 25, dt.datetime(2022, 2, 1)),
        ],
        ids=[
            "forward one month",
            "back one month",
            "across year end forward",
            "across year end backward",
            "multi-year shift",
        ],
    )
    def test_ordinary_shifts(self, start: dt.datetime, months: int, expected: dt.datetime) -> None:
        """Test that a day that exists in the target month is kept as-is."""
        assert month_shift(start, months) == expected

    @pytest.mark.parametrize(
        "start,months,expected",
        [
            (dt.datetime(2023, 1, 31), 1, dt.datetime(2023, 2, 28)),
            (dt.datetime(2020, 1, 31), 1, dt.datetime(2020, 2, 29)),
            (dt.datetime(2020, 2, 29), 12, dt.datetime(2021, 2, 28)),
            (dt.datetime(2020, 2, 29), 48, dt.datetime(2024, 2, 29)),
        ],
        ids=[
            "Jan 31 -> Feb 28",
            "Jan 31 -> Feb 29 in a leap year",
            "12 months from a leap day clamps",
            "48 months from a leap day lands on another leap day",
        ],
    )
    def test_end_of_month_clamping(self, start: dt.datetime, months: int, expected: dt.datetime) -> None:
        """Test that a day past the end of the target month is clamped to that month's last day."""
        assert month_shift(start, months) == expected

    def test_time_of_day_is_preserved(self) -> None:
        """Test that only the date part moves; hours/minutes/seconds/microseconds are untouched, including when clamping
        a day that doesn't exist in the target month."""
        result = month_shift(dt.datetime(2020, 2, 29, 23, 59, 59, 999_999), 12)
        assert result == dt.datetime(2021, 2, 28, 23, 59, 59, 999_999)


class TestAdvanceAndRetreat:
    def test_zero_offsets_are_a_no_op(self) -> None:
        """Test that with nothing to shift by, both return their input unchanged."""
        d = dt.datetime(2024, 1, 1)
        assert advance(d, month_offset=0, microsecond_offset=0) == d
        assert retreat(d, month_offset=0, microsecond_offset=0) == d

    def test_month_offset_retreat_undoes_advance(self) -> None:
        """Test that retreat(advance(x)) == x for a month-only offset."""
        original = dt.datetime(2024, 3, 31, 12, 0)
        advanced = advance(original, month_offset=9, microsecond_offset=0)
        assert retreat(advanced, month_offset=9, microsecond_offset=0) == original

    def test_year_multiple_month_offset_shifts_in_one_step(self) -> None:
        """Test that a 12-month offset shifts by a single 12-month step, clamping Feb 29 against the target year
        directly rather than composing twelve individual 1-month steps."""
        result = advance(dt.datetime(2020, 2, 29), month_offset=12, microsecond_offset=0)
        assert result == dt.datetime(2021, 2, 28)

    def test_microsecond_offset_retreat_undoes_advance(self) -> None:
        """Test that retreat(advance(x)) == x for a microsecond-only offset."""
        original = dt.datetime(2024, 1, 1)
        advanced = advance(original, month_offset=0, microsecond_offset=500_000)
        assert retreat(advanced, month_offset=0, microsecond_offset=500_000) == original

    def test_combined_offset_applies_and_reverses_in_the_right_order(self) -> None:
        """Test that advancing 1 month then 1 day from Apr 30 lands on May 31; retreat undoes it."""
        original = dt.datetime(2024, 4, 30)
        advanced = advance(original, month_offset=1, microsecond_offset=86_400_000_000)
        assert advanced == dt.datetime(2024, 5, 31)
        assert retreat(advanced, month_offset=1, microsecond_offset=86_400_000_000) == original


class TestNaive:
    def test_aware_datetime_loses_only_its_tzinfo(self) -> None:
        """Test that the date and time fields are untouched; only tzinfo is dropped."""
        aware = dt.datetime(2024, 3, 1, 9, 30, 15, 123_456, tzinfo=dt.UTC)
        assert naive(aware) == dt.datetime(2024, 3, 1, 9, 30, 15, 123_456)

    def test_already_naive_datetime_is_unchanged(self) -> None:
        """Test that a datetime with no tzinfo compares equal to itself after the call."""
        d = dt.datetime(2024, 3, 1, 9, 30)
        assert naive(d) == d

    def test_two_offsets_become_comparable(self) -> None:
        """Test that the point of naive(): wall-clock times in different zones can be subtracted."""
        utc = dt.datetime(2024, 3, 1, 9, tzinfo=dt.UTC)
        plus5 = dt.datetime(2024, 3, 1, 9, tzinfo=dt.timezone(dt.timedelta(hours=5)))
        assert naive(utc) - naive(plus5) == dt.timedelta(0)


class TestTotalMicroseconds:
    @pytest.mark.parametrize(
        "delta,expected",
        [
            (dt.timedelta(0), 0),
            (dt.timedelta(microseconds=1), 1),
            (dt.timedelta(seconds=1), 1_000_000),
            (dt.timedelta(days=1), 86_400_000_000),
            (dt.timedelta(days=1, seconds=1, microseconds=1), 86_401_000_001),
            (dt.timedelta(microseconds=-1), -1),
            (dt.timedelta(days=-1), -86_400_000_000),
        ],
        ids=["zero", "1us", "1s", "1d", "mixed", "negative us", "negative day"],
    )
    def test_render(self, delta: dt.timedelta, expected: int) -> None:
        """Test that every component is folded into the microsecond total, sign included."""
        assert total_microseconds(delta) == expected

    def test_matches_the_timedelta_components(self) -> None:
        """Test that the result agrees with timedelta's own days/seconds/microseconds breakdown."""
        delta = dt.timedelta(days=3, seconds=45, microseconds=678)
        assert total_microseconds(delta) == (3 * 86_400 + 45) * 1_000_000 + 678


class TestGregorianSeconds:
    def test_day_epoch_is_the_day_before_year_one(self) -> None:
        """Test that January 1 of year 1 is exactly one day after the epoch."""
        assert gregorian_seconds(dt.datetime(1, 1, 1)) == 86_400

    @pytest.mark.parametrize(
        "delta",
        [dt.timedelta(seconds=1), dt.timedelta(hours=1), dt.timedelta(days=1), dt.timedelta(days=400)],
        ids=["1s", "1h", "1d", "400d"],
    )
    def test_differences_match_the_elapsed_seconds(self, delta: dt.timedelta) -> None:
        """Test that subtracting two results gives the real number of seconds between them."""
        start = dt.datetime(2024, 3, 1, 9, 30, 15)
        assert gregorian_seconds(start + delta) - gregorian_seconds(start) == delta // dt.timedelta(seconds=1)

    def test_sub_second_component_is_ignored(self) -> None:
        """Test that the timeline is in whole seconds, so microseconds do not move it."""
        assert gregorian_seconds(dt.datetime(2024, 3, 1, 9, 30, 15, 999_999)) == gregorian_seconds(
            dt.datetime(2024, 3, 1, 9, 30, 15)
        )

    def test_tzinfo_is_ignored(self) -> None:
        """Test that only the wall-clock fields are read; the offset plays no part."""
        d = dt.datetime(2024, 3, 1, 9, 30, 15)
        assert gregorian_seconds(d.replace(tzinfo=dt.UTC)) == gregorian_seconds(d)


class TestMonthOrdinalAndYearMonth:
    @pytest.mark.parametrize(
        "date_time,expected",
        [
            (dt.datetime(1, 1, 1), 12),
            (dt.datetime(1, 2, 1), 13),
            (dt.datetime(2, 1, 1), 24),
            (dt.datetime(2024, 3, 15), 2024 * 12 + 2),
        ],
        ids=["january of year one", "second month", "second year", "modern"],
    )
    def test_month_ordinal(self, date_time: dt.datetime, expected: int) -> None:
        """Test that the ordinal counts whole months from the start of year 0."""
        assert month_ordinal(date_time) == expected

    def test_day_and_time_do_not_affect_the_ordinal(self) -> None:
        """Test that every instant within a month shares that month's ordinal."""
        assert month_ordinal(dt.datetime(2024, 3, 1)) == month_ordinal(dt.datetime(2024, 3, 31, 23, 59, 59))

    def test_round_trip_over_three_millennia(self) -> None:
        """Test that year_month undoes month_ordinal for every month of years 1-2999."""
        assert all(
            year_month(month_ordinal(dt.datetime(year, month, 1))) == (year, month)
            for year in range(1, 3000)
            for month in range(1, 13)
        )

    def test_year_month_returns_a_one_based_month(self) -> None:
        """Test that the month component comes back in the usual 1-12 range, not 0-11."""
        assert year_month(12) == (1, 1)
        assert year_month(23) == (1, 12)
