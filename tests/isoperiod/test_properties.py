import datetime as dt

import pytest

from isoperiod.enums import Precision, Step
from isoperiod.exceptions import PeriodConfigError, PeriodValidationError
from isoperiod.properties import Properties


def months(multiplier: int, month_offset: int = 0, microsecond_offset: int = 0) -> Properties:
    """A raw MONTHS-step Properties (no normalisation, no validation beyond __post_init__)."""
    return Properties(
        step=Step.MONTHS,
        multiplier=multiplier,
        month_offset=month_offset,
        microsecond_offset=microsecond_offset,
        tzinfo=None,
        ordinal_shift=0,
    )


def seconds(multiplier: int, microsecond_offset: int = 0) -> Properties:
    """A raw SECONDS-step Properties."""
    return Properties(
        step=Step.SECONDS,
        multiplier=multiplier,
        month_offset=0,
        microsecond_offset=microsecond_offset,
        tzinfo=None,
        ordinal_shift=0,
    )


def micros(multiplier: int, microsecond_offset: int = 0) -> Properties:
    """A raw MICROSECONDS-step Properties."""
    return Properties(
        step=Step.MICROSECONDS,
        multiplier=multiplier,
        month_offset=0,
        microsecond_offset=microsecond_offset,
        tzinfo=None,
        ordinal_shift=0,
    )


def _mutated(base: Properties, **overrides: object) -> Properties:
    """A copy of `base` with fields forced past the validation in __post_init__."""
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


class TestPostInit:
    def test_illegal_step_rejected(self) -> None:
        """Test that a step outside the Step enum raises PeriodValidationError."""
        with pytest.raises(PeriodValidationError):
            Properties(step=99, multiplier=1, month_offset=0, microsecond_offset=0, tzinfo=None, ordinal_shift=0)

    def test_non_positive_multiplier_rejected(self) -> None:
        """Test that a multiplier of zero (or less) is not a valid period length."""
        with pytest.raises(PeriodValidationError):
            seconds(0)

    def test_negative_month_offset_rejected(self) -> None:
        """Test that a month offset must be zero or greater."""
        with pytest.raises(PeriodValidationError):
            months(1, month_offset=-1)

    def test_negative_microsecond_offset_rejected(self) -> None:
        """Test that a microsecond offset must be zero or greater."""
        with pytest.raises(PeriodValidationError):
            seconds(1, microsecond_offset=-1)

    def test_month_offset_on_non_month_step_rejected(self) -> None:
        """Test that only a MONTHS-step period may carry a month offset."""
        with pytest.raises(PeriodValidationError):
            Properties(
                step=Step.SECONDS, multiplier=1, month_offset=1, microsecond_offset=0, tzinfo=None, ordinal_shift=0
            )


class TestNormaliseOffsets:
    @pytest.mark.parametrize(
        "multiplier,offset,expected",
        [(12, 13, 1), (12, 24, 0), (12, 6, 6)],
        ids=["13 months on a 12-month period -> 1", "exact multiple -> 0", "already in range"],
    )
    def test_month_offset_wraps_around_multiplier(self, multiplier: int, offset: int, expected: int) -> None:
        """Test that a MONTHS-step offset is taken modulo the multiplier."""
        assert months(multiplier, month_offset=offset).normalise_offsets().month_offset == expected

    def test_microsecond_offset_wraps_around_a_seconds_period(self) -> None:
        """Test that a 30-second offset on a 10-second period has no net effect."""
        assert seconds(10, microsecond_offset=30_000_000).normalise_offsets().microsecond_offset == 0

    @pytest.mark.parametrize(
        "offset,expected",
        [(1_200, 200), (1_000, 0)],
        ids=["not a multiple", "exact multiple -> 0"],
    )
    def test_microsecond_offset_wraps_around_a_microseconds_period(self, offset: int, expected: int) -> None:
        """Test that a MICROSECONDS-step offset is taken modulo the multiplier."""
        assert micros(500, microsecond_offset=offset).normalise_offsets().microsecond_offset == expected

    def test_already_normalised_returns_self(self) -> None:
        """Test that when nothing changes, the same object is returned."""
        props = months(12, month_offset=3)
        assert props.normalise_offsets() is props

    def test_resets_ordinal_shift(self) -> None:
        """Test that Re-basing the offset invalidates any ordinal shift, so it is zeroed."""
        props = Properties(
            step=Step.MONTHS, multiplier=12, month_offset=13, microsecond_offset=0, tzinfo=None, ordinal_shift=5
        )
        assert props.normalise_offsets().ordinal_shift == 0

    @pytest.mark.parametrize("step", [Step.SECONDS, Step.MICROSECONDS], ids=["seconds", "microseconds"])
    def test_month_offset_on_a_time_based_step_is_rejected(self, step: int) -> None:
        """Test that a corrupt time-based Properties carrying a month offset is caught here too."""
        with pytest.raises(PeriodValidationError):
            _mutated(seconds(10), step=step, month_offset=5).normalise_offsets()


class TestWithMonthOffset:
    def test_adds_to_existing_offset(self) -> None:
        """Test that the argument is added to whatever month offset is already set."""
        assert months(12, month_offset=3).with_month_offset(2).month_offset == 5

    def test_result_is_normalised(self) -> None:
        """Test that 15 months on a 12-month period normalises to 3."""
        assert months(12).with_month_offset(15).month_offset == 3

    def test_resets_ordinal_shift(self) -> None:
        """Test that changing the offset zeroes any previous ordinal shift."""
        props = Properties(
            step=Step.MONTHS, multiplier=12, month_offset=0, microsecond_offset=0, tzinfo=None, ordinal_shift=5
        )
        assert props.with_month_offset(1).ordinal_shift == 0


class TestWithMicrosecondOffset:
    def test_adds_to_existing_offset(self) -> None:
        """Test that the argument is added to the current microsecond offset."""
        result = seconds(10, microsecond_offset=1_000_000).with_microsecond_offset(1_000_000)
        assert result.microsecond_offset == 2_000_000

    def test_result_is_normalised(self) -> None:
        """Test that 35 seconds of offset on a 10-second period normalises to 5."""
        assert seconds(10).with_microsecond_offset(35_000_000).microsecond_offset == 5_000_000


class TestWithTzinfo:
    def test_sets_tzinfo(self) -> None:
        """Test that the tzinfo is stored on the returned Properties."""
        assert seconds(1).with_tzinfo(dt.UTC).tzinfo == dt.UTC

    def test_same_value_still_returns_an_equal_object(self) -> None:
        """Test that unlike Period.with_tzinfo, there is no identity short-circuit here."""
        props = seconds(1)
        assert props.with_tzinfo(None) == props

    def test_preserves_ordinal_shift(self) -> None:
        """Test that setting a timezone leaves the ordinal shift untouched."""
        props = Properties(
            step=Step.SECONDS, multiplier=1, month_offset=0, microsecond_offset=0, tzinfo=None, ordinal_shift=7
        )
        assert props.with_tzinfo(dt.UTC).ordinal_shift == 7


class TestWithOrdinalShift:
    def test_sets_shift(self) -> None:
        """Test that the shift value is stored verbatim."""
        assert seconds(1).with_ordinal_shift(42).ordinal_shift == 42


class TestGetIso8601:
    @pytest.mark.parametrize(
        "props,expected",
        [(months(12), "P1Y"), (months(3), "P3M"), (seconds(3_600), "PT1H"), (micros(1), "PT0.000001S")],
        ids=["1 year", "3 months", "1 hour", "1 microsecond"],
    )
    def test_render(self, props: Properties, expected: str) -> None:
        """Test that each step renders through its matching iso.py period-name helper."""
        assert props.get_iso8601() == expected


class TestGetTimedelta:
    def test_seconds_step(self) -> None:
        """Test that a seconds period maps straight onto a timedelta."""
        assert seconds(90).get_timedelta() == dt.timedelta(seconds=90)

    def test_microseconds_step(self) -> None:
        """Test that a microseconds period splits into whole seconds plus a microseconds remainder."""
        assert micros(1_500_000).get_timedelta() == dt.timedelta(seconds=1, microseconds=500_000)

    def test_months_step_has_no_fixed_timedelta(self) -> None:
        """Test that months vary in length, so there is no single timedelta."""
        assert months(1).get_timedelta() is None


class TestIsEpochAgnostic:
    @pytest.mark.parametrize(
        "n,expected",
        [(1, True), (2, True), (3, True), (4, True), (5, False), (6, True), (7, False), (12, True), (13, False)],
        ids=[f"{n}mo" for n in (1, 2, 3, 4, 5, 6, 7, 12, 13)],
    )
    def test_months(self, n: int, expected: bool) -> None:
        """Test that an n-month period is agnostic iff n divides 12."""
        assert months(n).is_epoch_agnostic() is expected

    @pytest.mark.parametrize(
        "n,expected",
        [
            (1, True),
            (2, True),
            (3, True),
            (4, True),
            (5, False),
            (6, True),
            (7, False),
            (8, True),
            (9, False),
            (12, True),
            (24, True),
        ],
        ids=[f"{n}h" for n in (1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 24)],
    )
    def test_hours(self, n: int, expected: bool) -> None:
        """Test that an n-hour period is agnostic iff n hours divide a day."""
        assert seconds(n * 3_600).is_epoch_agnostic() is expected

    @pytest.mark.parametrize(
        "multiplier,expected",
        [(500_000, True), (1_500_000, False)],
        ids=["half a second", "1.5 seconds (divides a day but still not agnostic)"],
    )
    def test_microsecond_periods(self, multiplier: int, expected: bool) -> None:
        """Test that a microsecond period is agnostic only if it is at most one second and divides a day."""
        assert micros(multiplier).is_epoch_agnostic() is expected


class TestCount:
    def test_same_period_is_one(self) -> None:
        """Test that a period fits itself exactly once."""
        assert seconds(60).count(seconds(60)) == 1

    def test_different_tzinfo_is_unaligned(self) -> None:
        """Test that periods over different timezones are never aligned."""
        aware = Properties(
            step=Step.SECONDS, multiplier=60, month_offset=0, microsecond_offset=0, tzinfo=dt.UTC, ordinal_shift=0
        )
        assert seconds(60).count(aware) == -1

    def test_seconds_within_seconds(self) -> None:
        """Test that an hour contains 24 hours' worth... i.e. a day holds 24 hourly intervals."""
        assert seconds(3_600).count(seconds(86_400)) == 24

    def test_seconds_within_months_is_aligned_but_unknown(self) -> None:
        """Test that a day aligns to a month boundary but months have no constant day count."""
        assert seconds(86_400).count(months(1)) == 0

    @pytest.mark.parametrize(
        "self_props,other_props,expected",
        [
            (seconds(3_600), months(1, microsecond_offset=1_800_000_000), -1),
            (seconds(86_400), months(12, month_offset=9, microsecond_offset=32_400_000_000), -1),
            (seconds(86_400, microsecond_offset=32_400_000_000), months(12, month_offset=9), -1),
            (seconds(3_600), months(1, microsecond_offset=3_600_000_000), 0),
            (
                seconds(86_400, microsecond_offset=32_400_000_000),
                months(12, month_offset=9, microsecond_offset=32_400_000_000),
                0,
            ),
        ],
        ids=[
            "hours vs month offset by 30 minutes",
            "days vs water year (09:00 boundary)",
            "water days vs plain year (midnight boundary)",
            "hours vs month offset by a whole hour",
            "water days vs water year",
        ],
    )
    def test_seconds_within_offset_months(self, self_props: Properties, other_props: Properties, expected: int) -> None:
        """Test that a seconds period aligns to an offset months period only if the offsets differ by a whole
        number of self-intervals.

        The offsets are held in microseconds, so the multipliers must be compared in microseconds too - a
        seconds-unit comparison here wrongly reports a 30-minute offset as aligned to an hourly period.
        """
        assert self_props.count(other_props) == expected

    def test_months_within_months(self) -> None:
        """Test that a month fits 12 times in a year."""
        assert months(1).count(months(12)) == 12

    def test_second_cannot_fit_evenly_in_a_microsecond_period(self) -> None:
        """Test that a whole-second period never divides a (sub-second-step) microsecond period."""
        two_seconds_as_micro = micros(2_000_000)
        assert seconds(1).count(two_seconds_as_micro) == -1

    @pytest.mark.parametrize(
        "other",
        [seconds(86_400), micros(500)],
        ids=["seconds period", "microseconds period"],
    )
    def test_months_never_fit_evenly_in_a_time_based_period(self, other: Properties) -> None:
        """Test that a month has no fixed length, so it can't tile a fixed-length period."""
        assert months(1).count(other) == -1

    def test_zero_self_offset_but_unaligned_other_offset_is_unaligned(self) -> None:
        """Test that `self` has no offset; `other`'s offset isn't a whole number of self-intervals."""
        assert seconds(3_600).count(seconds(86_400, microsecond_offset=1_000_000)) == -1


class TestPolarsStrings:
    @pytest.mark.parametrize(
        "props,expected",
        [(micros(40_000), "40000us"), (seconds(60), "60s"), (months(3), "3mo")],
        ids=["microseconds", "seconds", "months"],
    )
    def test_pl_interval(self, props: Properties, expected: str) -> None:
        """Test that pl_interval names the step/multiplier in Polars units."""
        assert props.pl_interval() == expected

    def test_pl_offset_combines_month_and_microsecond_parts(self) -> None:
        """Test that pl_offset always emits both a `mo` and a `us` term."""
        assert months(12, month_offset=3, microsecond_offset=500_000).pl_offset() == "3mo500000us"


class TestOffsetString:
    @pytest.mark.parametrize(
        "props,expected",
        [
            (seconds(10), ""),
            (months(12, month_offset=3), "+3M"),
            (seconds(10, microsecond_offset=500_000), "+T0.5S"),
            (months(12, month_offset=9, microsecond_offset=9 * 3_600 * 1_000_000), "+9MT32400S"),
        ],
        ids=["no offset", "month offset only", "sub-second offset only", "month and time offset"],
    )
    def test_render(self, props: Properties, expected: str) -> None:
        """Test that no offset yields an empty string; otherwise a '+' prefix with the parts present."""
        assert props.offset() == expected


class TestStrAndRepr:
    @pytest.mark.parametrize(
        "props,expected",
        [
            (micros(1_500_000), "PT1.5S"),
            (months(12, month_offset=3), "P1Y+3M"),
            (seconds(10, microsecond_offset=500_000), "PT10S+T0.5S"),
        ],
        ids=["microsecond period", "month offset only", "microsecond offset only"],
    )
    def test_str(self, props: Properties, expected: str) -> None:
        """Test that str() joins the step elements and any offset elements."""
        assert str(props) == expected

    def test_repr_appends_timezone_and_shift(self) -> None:
        """Test that repr() adds the [tz] bracket and a trailing shift when present."""
        props = seconds(1).with_tzinfo(dt.UTC).with_ordinal_shift(5)
        assert repr(props) == "PT1S[Z]5"

    def test_repr_of_offsetless_timezone_has_empty_brackets(self) -> None:
        """Test that a tzinfo that can't report an offset renders as an empty '[]'."""

        class _NoOffsetTZ(dt.tzinfo):
            def utcoffset(self, _: dt.datetime | None) -> dt.timedelta | None:
                return None

            def tzname(self, _: dt.datetime | None) -> str:
                return "weird"

            def dst(self, _: dt.datetime | None) -> dt.timedelta | None:
                return None

        assert repr(seconds(1).with_tzinfo(_NoOffsetTZ())).endswith("[]")


class TestNaivePrecisionSelection:
    @pytest.mark.parametrize(
        "props,expected",
        [
            (Properties.of_months(12), Precision.YEAR),
            (Properties.of_months(1), Precision.MONTH),
            (Properties.of_seconds(86_400), Precision.DAY),
            (Properties.of_seconds(3_600), Precision.HOUR),
            (Properties.of_seconds(900), Precision.MINUTE),
            (Properties.of_seconds(30), Precision.SECOND),
            (micros(2_000_000), Precision.SECOND),
            (micros(1_500_000), Precision.MILLISECOND),
            (Properties.of_microseconds(1), Precision.MICROSECOND),
        ],
        ids=[
            "year",
            "month",
            "day",
            "hour",
            "minute",
            "second",
            "whole-second us step",
            "millisecond us step",
            "microsecond us step",
        ],
    )
    def test_multiplier_driven(self, props: Properties, expected: Precision) -> None:
        """Test that with no offset, the multiplier alone decides the precision."""
        assert props._naive_precision() == expected

    @pytest.mark.parametrize(
        "props,expected",
        [
            (seconds(10, microsecond_offset=1), Precision.MICROSECOND),
            (seconds(10, microsecond_offset=500_000), Precision.MILLISECOND),
            (micros(1_000_000, microsecond_offset=1_000), Precision.MILLISECOND),
            (months(12, microsecond_offset=5_000_000), Precision.SECOND),
            (months(12, microsecond_offset=5 * 60 * 1_000_000), Precision.MINUTE),
            (months(12, microsecond_offset=5 * 3_600 * 1_000_000), Precision.HOUR),
            (months(12, microsecond_offset=2 * 86_400 * 1_000_000), Precision.DAY),
        ],
        ids=[
            "sub-ms offset",
            "ms offset",
            "ms offset on us step",
            "s offset",
            "min offset",
            "hour offset",
            "day offset",
        ],
    )
    def test_offset_driven(self, props: Properties, expected: Precision) -> None:
        """Test that an offset widens the precision past what the multiplier alone would need."""
        assert props._naive_precision() == expected


class TestAwarePrecisionSelection:
    @pytest.mark.parametrize(
        "props,expected",
        [
            (Properties.of_months(12), Precision.HOUR),
            (Properties.of_months(1), Precision.HOUR),
            (Properties.of_seconds(86_400), Precision.HOUR),
            (Properties.of_seconds(3_600), Precision.HOUR),
            (Properties.of_seconds(900), Precision.MINUTE),
            (seconds(90), Precision.SECOND),
            (micros(1), Precision.MICROSECOND),
            (micros(500_000), Precision.MILLISECOND),
            (micros(2_000_000), Precision.SECOND),
        ],
        ids=[
            "year -> HOUR",
            "month -> HOUR",
            "day -> HOUR",
            "hour",
            "minute",
            "non-whole-minute seconds",
            "sub-ms us step",
            "sub-second us step",
            "whole-second us step",
        ],
    )
    def test_multiplier_driven(self, props: Properties, expected: Precision) -> None:
        """Test that the multiplier decides the precision, floored at HOUR."""
        assert props._aware_precision() == expected

    @pytest.mark.parametrize(
        "props,expected",
        [
            (seconds(10, microsecond_offset=500_001), Precision.MICROSECOND),
            (seconds(10, microsecond_offset=500_000), Precision.MILLISECOND),
            (months(12, microsecond_offset=5_000_000), Precision.SECOND),
            (months(12, microsecond_offset=5 * 60 * 1_000_000), Precision.MINUTE),
            (months(12, microsecond_offset=5 * 3_600 * 1_000_000), Precision.HOUR),
        ],
        ids=["sub-ms offset", "ms offset", "s offset", "min offset", "hour offset"],
    )
    def test_offset_driven(self, props: Properties, expected: Precision) -> None:
        """Test that an offset widens the precision, still floored at HOUR."""
        assert props._aware_precision() == expected


class TestStepDispatchGuards:
    @pytest.mark.parametrize(
        "call",
        [
            lambda p: p.get_iso8601(),
            lambda p: p.get_timedelta(),
            lambda p: p._append_step_elems([]),
            lambda p: p.normalise_offsets(),
            lambda p: p.pl_interval(),
            lambda p: p.is_epoch_agnostic(),
            lambda p: p._naive_precision(),
            lambda p: p._aware_precision(),
        ],
        ids=[
            "get_iso8601",
            "get_timedelta",
            "_append_step_elems",
            "normalise_offsets",
            "pl_interval",
            "is_epoch_agnostic",
            "_naive_precision",
            "_aware_precision",
        ],
    )
    def test_bad_step_is_rejected(self, call) -> None:
        """Test that each step-dispatch method raises when a corrupt Properties, with a step forced past
        __post_init__, reaches its final branch."""
        with pytest.raises((PeriodValidationError, PeriodConfigError)):
            call(_mutated(seconds(10), step=999))
