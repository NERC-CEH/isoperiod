import datetime as dt

import pytest

from isoperiod.enums import Precision
from isoperiod.exceptions import PeriodParsingError
from isoperiod.formatting import format_aware, format_naive, format_tzdelta, format_tzinfo

_SAMPLE = dt.datetime(2024, 3, 1, 5, 15, 30, 123_456)
_SAMPLE_UTC = _SAMPLE.replace(tzinfo=dt.UTC)


class TestPrecisionEnum:
    def test_members_increase_from_year_to_microsecond(self) -> None:
        """Test that comparing members reflects coarse-to-fine ordering."""
        assert (
            Precision.YEAR
            < Precision.MONTH
            < Precision.DAY
            < Precision.HOUR
            < Precision.MINUTE
            < Precision.SECOND
            < Precision.MILLISECOND
            < Precision.MICROSECOND
        )


class TestFormatNaive:
    @pytest.mark.parametrize(
        "precision,expected",
        [
            (Precision.YEAR, "2024"),
            (Precision.MONTH, "2024-03"),
            (Precision.DAY, "2024-03-01"),
            (Precision.HOUR, "2024-03-01T05"),
            (Precision.MINUTE, "2024-03-01T05:15"),
            (Precision.SECOND, "2024-03-01T05:15:30"),
            (Precision.MILLISECOND, "2024-03-01T05:15:30.123"),
            (Precision.MICROSECOND, "2024-03-01T05:15:30.123456"),
        ],
        ids=["year", "month", "day", "hour", "minute", "second", "millisecond", "microsecond"],
    )
    def test_precision_levels(self, precision: Precision, expected: str) -> None:
        """Test that each precision keeps exactly its components and drops everything finer."""
        assert format_naive(_SAMPLE, precision) == expected

    def test_ignores_any_tzinfo_on_the_input(self) -> None:
        """Test that format_naive is documented to take a naive datetime; if it's handed a timezone-aware one anyway,
        the tzinfo is silently ignored rather than appended."""
        assert format_naive(_SAMPLE_UTC, Precision.SECOND) == format_naive(_SAMPLE, Precision.SECOND)


class TestFormatAware:
    @pytest.mark.parametrize(
        "precision,expected",
        [
            (Precision.HOUR, "2024-03-01T05Z"),
            (Precision.MINUTE, "2024-03-01T05:15Z"),
            (Precision.SECOND, "2024-03-01T05:15:30Z"),
            (Precision.MILLISECOND, "2024-03-01T05:15:30.123Z"),
            (Precision.MICROSECOND, "2024-03-01T05:15:30.123456Z"),
        ],
        ids=["hour", "minute", "second", "millisecond", "microsecond"],
    )
    def test_precision_levels_with_utc(self, precision: Precision, expected: str) -> None:
        """Test that a UTC datetime renders the offset as a trailing 'Z' at every precision."""
        assert format_aware(_SAMPLE_UTC, precision) == expected

    @pytest.mark.parametrize(
        "precision", [Precision.YEAR, Precision.MONTH, Precision.DAY], ids=["year", "month", "day"]
    )
    def test_precision_coarser_than_hour_is_clamped_to_hour(self, precision: Precision) -> None:
        """Test that a bare date can't carry an offset, so anything coarser than HOUR renders as HOUR."""
        assert format_aware(_SAMPLE_UTC, precision) == "2024-03-01T05Z"

    def test_non_utc_offset_is_rendered_as_hh_mm(self) -> None:
        """Test that a non-UTC offset is rendered as +/-HH:MM after the time."""
        tz = dt.timezone(dt.timedelta(hours=5, minutes=30))
        assert format_aware(_SAMPLE.replace(tzinfo=tz), Precision.HOUR) == "2024-03-01T05+05:30"

    def test_naive_datetime_produces_no_timezone_suffix(self) -> None:
        """Test that passed a naive datetime, format_aware simply omits the timezone part."""
        assert format_aware(_SAMPLE, Precision.HOUR) == "2024-03-01T05"


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


class _NoOffsetTZ(dt.tzinfo):
    """A tzinfo whose utcoffset is unknown (returns None)."""

    def utcoffset(self, _: dt.datetime | None) -> dt.timedelta | None:
        return None

    def tzname(self, _: dt.datetime | None) -> str:
        return "weird"

    def dst(self, _: dt.datetime | None) -> dt.timedelta | None:
        return None


class TestFormatTzinfo:
    def test_none_gives_empty_string(self) -> None:
        """Test that no timezone means no suffix."""
        assert format_tzinfo(None) == ""

    def test_offsetless_tzinfo_gives_empty_string(self) -> None:
        """Test that a tzinfo that cannot report an offset also yields no suffix."""
        assert format_tzinfo(_NoOffsetTZ()) == ""

    @pytest.mark.parametrize(
        "tz,expected",
        [
            (dt.UTC, "Z"),
            (dt.timezone(dt.timedelta(hours=1)), "+01:00"),
            (dt.timezone(dt.timedelta(hours=-3, minutes=-30)), "-03:30"),
        ],
        ids=["utc", "+01:00", "-03:30"],
    )
    def test_known_offset_is_delegated_to_format_tzdelta(self, tz: dt.tzinfo, expected: str) -> None:
        """Test that a tzinfo with a known offset renders the same as its raw delta."""
        assert format_tzinfo(tz) == expected
