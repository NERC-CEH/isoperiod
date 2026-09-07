import datetime as dt
import re

import pytest

from isoperiod.exceptions import PeriodParsingError
from isoperiod.iso import (
    append_month_elems,
    append_second_elems,
    format_tzdelta,
    microsecond_period_name,
    month_period_name,
    period_regex,
    second_period_name,
    second_string,
)


class TestSecondString:
    @pytest.mark.parametrize(
        "seconds,microseconds,expected",
        [
            (0, 0, "0"),
            (30, 0, "30"),
            (1, 500_000, "1.5"),
            (0, 500_000, "0.5"),
            (10, 1, "10.000001"),
            (10, 123_400, "10.1234"),
        ],
        ids=["zero", "whole seconds", "half second", "sub-second only", "one microsecond", "trailing zeros trimmed"],
    )
    def test_render(self, seconds: int, microseconds: int, expected: str) -> None:
        """Test that a whole number keeps no decimal point; a fraction is trimmed of trailing zeros."""
        assert second_string(seconds, microseconds) == expected


class TestAppendSecondElems:
    @pytest.mark.parametrize(
        "seconds,microseconds,expected",
        [
            (0, 0, "P"),
            (1, 0, "PT1S"),
            (90, 0, "PT1M30S"),
            (3_600, 0, "PT1H"),
            (86_400, 0, "P1D"),
            (90_061, 0, "P1DT1H1M1S"),
            (0, 500_000, "PT0.5S"),
            (1, 500_000, "PT1.5S"),
        ],
        ids=["empty", "1s", "1m30s", "1h", "1d", "1d1h1m1s", "half second", "1.5s"],
    )
    def test_fragments(self, seconds: int, microseconds: int, expected: str) -> None:
        """Test that joining the appended fragments onto a leading 'P' yields the duration string."""
        assert "".join(append_second_elems(["P"], seconds, microseconds)) == expected

    def test_returns_the_same_list_it_was_given(self) -> None:
        """Test that the list is mutated in place and also returned for convenience."""
        elems: list[str] = ["P"]
        assert append_second_elems(elems, 1, 0) is elems


class TestAppendMonthElems:
    @pytest.mark.parametrize(
        "months,expected",
        [(0, "P"), (1, "P1M"), (11, "P11M"), (12, "P1Y"), (13, "P1Y1M"), (24, "P2Y")],
        ids=["empty", "1 month", "11 months", "1 year", "1 year 1 month", "2 years"],
    )
    def test_fragments(self, months: int, expected: str) -> None:
        """Test that whole years become nY; the remainder becomes nM."""
        assert "".join(append_month_elems(["P"], months)) == expected


class TestPeriodNames:
    @pytest.mark.parametrize(
        "total_microseconds,expected",
        [(1, "PT0.000001S"), (500_000, "PT0.5S"), (1_000_000, "PT1S"), (1_500_000, "PT1.5S")],
        ids=["1us", "0.5s", "1s", "1.5s"],
    )
    def test_microsecond_period_name(self, total_microseconds: int, expected: str) -> None:
        """Test that a microsecond total is rendered as a (possibly fractional) seconds duration."""
        assert microsecond_period_name(total_microseconds) == expected

    @pytest.mark.parametrize(
        "seconds,expected",
        [(1, "PT1S"), (60, "PT1M"), (3_600, "PT1H"), (86_400, "P1D")],
        ids=["1s", "1m", "1h", "1d"],
    )
    def test_second_period_name(self, seconds: int, expected: str) -> None:
        """Test that a seconds total is rendered using the largest whole units that fit."""
        assert second_period_name(seconds) == expected

    @pytest.mark.parametrize(
        "months,expected",
        [(1, "P1M"), (3, "P3M"), (12, "P1Y"), (18, "P1Y6M")],
        ids=["1m", "3m", "1y", "1y6m"],
    )
    def test_month_period_name(self, months: int, expected: str) -> None:
        """Test that a months total is rendered as years plus residual months."""
        assert month_period_name(months) == expected


class TestPeriodRegex:
    def test_matches_a_full_duration_and_captures_named_groups(self) -> None:
        """Test that each date/time component is captured under its <prefix>_<unit> group."""
        match = re.fullmatch(period_regex("p"), "1Y2M3DT4H5M6.5S")
        assert match is not None
        assert match.group("p_years") == "1"
        assert match.group("p_months") == "2"
        assert match.group("p_days") == "3"
        assert match.group("p_hours") == "4"
        assert match.group("p_minutes") == "5"
        assert match.group("p_seconds") == "6"
        assert match.group("p_microseconds") == "5"

    def test_group_names_are_namespaced_by_prefix(self) -> None:
        """Test that two fragments with different prefixes can coexist in one pattern."""
        combined = re.compile(period_regex("a") + "/" + period_regex("b"))
        match = combined.fullmatch("1Y/2M")
        assert match is not None
        assert match.group("a_years") == "1"
        assert match.group("b_months") == "2"


class TestFormatTzdelta:
    @pytest.mark.parametrize(
        "delta,expected",
        [
            (dt.timedelta(0), "Z"),
            (dt.timedelta(hours=5, minutes=30), "+05:30"),
            (dt.timedelta(hours=-5), "-05:00"),
            (dt.timedelta(hours=-5, minutes=-30), "-05:30"),
        ],
        ids=["zero -> Z", "positive", "negative whole hour", "negative with minutes"],
    )
    def test_render(self, delta: dt.timedelta, expected: str) -> None:
        """Test that zero renders as 'Z'; anything else as a signed HH:MM."""
        assert format_tzdelta(delta) == expected

    def test_offset_of_a_day_or_more_is_rejected(self) -> None:
        """Test that an offset that reaches a whole day is not a valid timezone offset."""
        with pytest.raises(PeriodParsingError):
            format_tzdelta(dt.timedelta(days=1))

    def test_sub_minute_component_is_preserved(self) -> None:
        """Test that a (rare, but ISO 8601-legal) offset with seconds is rendered in full, not silently truncated to
        whole minutes."""
        assert format_tzdelta(dt.timedelta(hours=5, minutes=30, seconds=15)) == "+05:30:15"
