"""Tests for isoperiod/parsing.py: turning strings into Properties.

The public entry points are the Period.of* classmethods (thin delegators to the
parse_* functions here), so most cases are exercised through them; the
intermediate MonthsSeconds / PeriodFields dataclasses and the small string
helpers are tested directly.
"""

import datetime as dt

import pytest

from isoperiod import Period
from isoperiod.enums import Step
from isoperiod.exceptions import PeriodParsingError, PeriodValidationError
from isoperiod.parsing import MonthsSeconds, PeriodFields, str_to_int, str_to_microseconds


class TestStrToInt:
    @pytest.mark.parametrize(
        "value,default,expected",
        [("5", 0, 5), ("0", 0, 0), (None, 0, 0), (None, 1, 1)],
        ids=["digits", "zero", "None -> default 0", "None -> given default"],
    )
    def test_parse(self, value: str | None, default: int, expected: int) -> None:
        """Test that a string is converted to int; None falls back to the default."""
        assert str_to_int(value, default) == expected


class TestStrToMicroseconds:
    @pytest.mark.parametrize(
        "value,expected",
        [("5", 500_000), ("05", 50_000), ("000001", 1), ("123456", 123_456), (None, 0)],
        ids=["1 digit", "2 digits", "6 digits", "full precision", "None -> 0"],
    )
    def test_parse(self, value: str | None, expected: int) -> None:
        """Test that '.5' means 500000 microseconds; a missing fraction means 0."""
        assert str_to_microseconds(value) == expected


class TestMonthsSeconds:
    def test_rejects_a_negative_component(self) -> None:
        """Test that any negative months/seconds/microseconds is invalid."""
        with pytest.raises(PeriodValidationError):
            MonthsSeconds(string="P-1M", months=-1, seconds=0, microseconds=0)

    def test_rejects_out_of_range_microseconds(self) -> None:
        """Test that microseconds must be 0-999_999."""
        with pytest.raises(PeriodValidationError):
            MonthsSeconds(string="bad", months=0, seconds=0, microseconds=1_000_000)

    def test_rejects_an_all_zero_period(self) -> None:
        """Test that a period of no length at all is invalid."""
        with pytest.raises(PeriodValidationError):
            MonthsSeconds(string="P0D", months=0, seconds=0, microseconds=0)

    @pytest.mark.parametrize(
        "kwargs,expected",
        [
            ({"months": 6, "seconds": 0, "microseconds": 0}, (Step.MONTHS, 6)),
            ({"months": 0, "seconds": 90, "microseconds": 0}, (Step.SECONDS, 90)),
            ({"months": 0, "seconds": 1, "microseconds": 500_000}, (Step.MICROSECONDS, 1_500_000)),
        ],
        ids=["months", "seconds", "sub-second -> microseconds"],
    )
    def test_get_step_and_multiplier(self, kwargs: dict[str, int], expected: tuple[int, int]) -> None:
        """Test that a single populated unit maps to its Step and total multiplier."""
        assert MonthsSeconds(string="x", **kwargs).get_step_and_multiplier() == expected

    def test_get_step_and_multiplier_rejects_mixed_units(self) -> None:
        """Test that months and seconds together have no single-step representation."""
        with pytest.raises(PeriodValidationError):
            MonthsSeconds(string="P1M1S", months=1, seconds=1, microseconds=0).get_step_and_multiplier()

    def test_total_microseconds(self) -> None:
        """Test that total_microseconds folds seconds and microseconds into one figure."""
        assert MonthsSeconds(string="x", months=0, seconds=2, microseconds=500_000).total_microseconds() == 2_500_000


class TestPeriodFields:
    def test_rejects_a_negative_component(self) -> None:
        """Test that any negative field is invalid."""
        with pytest.raises(PeriodValidationError):
            PeriodFields(string="P-1Y", years=-1, months=0, days=0, hours=0, minutes=0, seconds=0, microseconds=0)

    def test_rejects_out_of_range_microseconds(self) -> None:
        """Test that microseconds must be 0-999_999."""
        with pytest.raises(PeriodValidationError):
            PeriodFields(string="bad", years=0, months=0, days=0, hours=0, minutes=0, seconds=0, microseconds=1_000_000)

    def test_get_months_seconds_folds_years_and_days(self) -> None:
        """Test that years roll into months; days/hours/minutes roll into seconds."""
        fields = PeriodFields(string="x", years=1, months=2, days=1, hours=1, minutes=1, seconds=1, microseconds=0)
        result = fields.get_months_seconds()
        assert (result.months, result.seconds) == (14, 90_061)


class TestOfIsoDuration:
    @pytest.mark.parametrize(
        "text,expected_iso",
        [
            ("P1Y", "P1Y"),
            ("P1M", "P1M"),
            ("P1D", "P1D"),
            ("P7D", "P7D"),
            ("PT1H", "PT1H"),
            ("PT15M", "PT15M"),
            ("PT1S", "PT1S"),
            ("PT0.5S", "PT0.5S"),
            ("PT0.000001S", "PT0.000001S"),
        ],
        ids=["year", "month", "day", "7 days", "hour", "15 min", "second", "half second", "1 microsecond"],
    )
    def test_valid(self, text: str, expected_iso: str) -> None:
        """Test that a well-formed single-unit duration round-trips through iso_duration."""
        assert Period.of_iso_duration(text).iso_duration == expected_iso

    def test_rejects_mixed_calendar_and_clock_units(self) -> None:
        """Test that a duration mixing months with days/time has no single-unit Period form."""
        with pytest.raises(PeriodValidationError):
            Period.of_iso_duration("P1Y2M3DT4H5M6S")

    @pytest.mark.parametrize("text", ["P0Y", "P0D", "PT0S"], ids=["zero years", "zero days", "zero seconds"])
    def test_rejects_zero_length(self, text: str) -> None:
        """Test that a syntactically valid but zero-length duration is rejected."""
        with pytest.raises(PeriodValidationError):
            Period.of_iso_duration(text)

    @pytest.mark.parametrize(
        "text",
        ["P-1Y", "PT0.0000001S", "not a duration", "1Y", "P1Y+3M", ""],
        ids=["negative", "below microsecond", "gibberish", "missing P", "offset form", "empty"],
    )
    def test_rejects_unparseable(self, text: str) -> None:
        """Test that a malformed string raises PeriodParsingError."""
        with pytest.raises(PeriodParsingError):
            Period.of_iso_duration(text)


class TestOfDuration:
    @pytest.mark.parametrize(
        "text,expected_repr",
        [
            ("P1D", "P1D[]"),
            ("P1D+T9H", "P1D+T9H[]"),
            ("P1Y+9MT9H", "P1Y+9MT9H[]"),
            ("PT10S+T0.5S", "PT10S+T0.5S[]"),
        ],
        ids=["plain", "day + hour offset", "water year", "sub-second offset"],
    )
    def test_valid(self, text: str, expected_repr: str) -> None:
        """Test that the parsed period reprs back to the canonical form."""
        assert repr(Period.of_duration(text)) == expected_repr

    @pytest.mark.parametrize(
        "text,expected_exception",
        [
            ("P0D+T9H", PeriodValidationError),
            ("P1D+", PeriodValidationError),
            ("garbage+T9H", PeriodParsingError),
        ],
        ids=["zero base period", "empty offset", "unparseable base"],
    )
    def test_invalid(self, text: str, expected_exception: type[Exception]) -> None:
        """Test that a bad base period or offset raises the appropriate error."""
        with pytest.raises(expected_exception):
            Period.of_duration(text)


class TestOfDateAndDuration:
    def test_sets_origin_from_datetime(self) -> None:
        """Test that the start datetime becomes ordinal 0 and is aligned."""
        p = Period.of_date_and_duration("1883-01-01T09:00:00/P1D")
        assert p.ordinal(dt.datetime(1883, 1, 1, 9, 0, 0)) == 0
        assert p.is_aligned(dt.datetime(1883, 1, 1, 9, 0, 0))

    def test_accepts_a_date_only_start(self) -> None:
        """Test that the time part of the start is optional."""
        p = Period.of_date_and_duration("2000-01-01/P1Y")
        assert p.ordinal(dt.datetime(2000, 1, 1)) == 0

    @pytest.mark.parametrize(
        "text,expected_start",
        [
            ("2000/P1Y", dt.datetime(2000, 1, 1)),
            ("2000-06/P1Y", dt.datetime(2000, 6, 1)),
        ],
        ids=["bare year", "year and month"],
    )
    def test_accepts_a_truncated_start(self, text: str, expected_start: dt.datetime) -> None:
        """Test that a bare year or year-month start is padded to the 1st, per ISO 8601 convention."""
        p = Period.of_date_and_duration(text)
        assert p.ordinal(expected_start) == 0

    def test_accepts_a_leap_day_start(self) -> None:
        """Test that a Feb 29 start in a genuine leap year parses."""
        p = Period.of_date_and_duration("2024-02-29T08:29:59.543Z/P1D")
        assert p.ordinal(dt.datetime(2024, 2, 29, 8, 29, 59, 543_000, tzinfo=dt.UTC)) == 0

    @pytest.mark.parametrize(
        "text,expected_offset",
        [
            ("2024-01-01T00:00:00Z/P1D", dt.timedelta(0)),
            ("2024-01-01T00:00:00+05/P1D", dt.timedelta(hours=5)),
            ("2024-01-01T00:00:00-05:30/P1D", dt.timedelta(hours=-5, minutes=-30)),
        ],
        ids=["Z", "whole hour, no colon", "negative offset"],
    )
    def test_carries_the_start_timezone_onto_the_period(self, text: str, expected_offset: dt.timedelta) -> None:
        """Test that the start's timezone (Z, +HH or +/-HH:MM) becomes the period's tzinfo."""
        p = Period.of_date_and_duration(text)
        assert p.tzinfo is not None
        assert p.tzinfo.utcoffset(None) == expected_offset

    @pytest.mark.parametrize(
        "text",
        [
            "1985-02-29T00:00:00/P1D",
            "2000-01-01",
            "2000-01-01/",
            "/P1D",
            "2000-13-01/P1D",
            "2000-01-01T25:00:00/P1D",
            "2000-1-01T00:00:00/P1D",
            "2000-01-01T00:00:00z/P1D",
            "2000-01-01T00:00:00+5/P1D",
        ],
        ids=[
            "invalid leap day",
            "missing /duration",
            "missing duration",
            "missing date",
            "invalid month",
            "invalid hour",
            "single-digit month",
            "lowercase z",
            "single-digit offset hour",
        ],
    )
    def test_invalid(self, text: str) -> None:
        """Test that a bad date, bad time, non-strict form, or missing half raises PeriodParsingError."""
        with pytest.raises(PeriodParsingError):
            Period.of_date_and_duration(text)

    @pytest.mark.parametrize(
        "text,expected_start",
        [
            ("20000101T000000Z/P1D", dt.datetime(2000, 1, 1, tzinfo=dt.UTC)),
            ("2000-W01-1/P1D", dt.datetime(2000, 1, 3)),
            (
                "2000-01-01T00:00:00+05:30:00/P1D",
                dt.datetime(2000, 1, 1, tzinfo=dt.timezone(dt.timedelta(hours=5, minutes=30))),
            ),
            ("2000-01-01X00:00:00/P1D", dt.datetime(2000, 1, 1)),
        ],
        ids=["basic format", "week date", "offset with seconds", "arbitrary separator"],
    )
    def test_start_accepts_whatever_fromisoformat_accepts(self, text: str, expected_start: dt.datetime) -> None:
        """Test that the start is delegated entirely to `datetime.fromisoformat`: forms it supports beyond the plain
        "yyyy-mm-ddTHH:MM:SS+HH:MM" shape - basic format, week dates, an offset with seconds, even a non-standard
        separator - are all accepted too."""
        p = Period.of_date_and_duration(text)
        assert p.ordinal(expected_start) == 0


class TestOf:
    @pytest.mark.parametrize(
        "text",
        ["P1D", "P1D+T9H", "1883-01-01/P1D"],
        ids=["plain iso", "extended offset", "date and duration"],
    )
    def test_accepts_any_supported_format(self, text: str) -> None:
        """Test that each of the three string formats is recognised."""
        assert Period.of(text) is not None

    def test_rejects_a_string_matching_no_format(self) -> None:
        """Test that a string that fits no format raises PeriodParsingError."""
        with pytest.raises(PeriodParsingError):
            Period.of("this matches no known format")
