import datetime as dt

import pytest

from isoperiod.enums import Step
from isoperiod.iso import append_month_elems, append_second_elems
from isoperiod.words import (
    frequency_word,
    join_words,
    month_words,
    origin_text,
    period_name,
    second_words,
)


class TestMonthWords:
    @pytest.mark.parametrize(
        "months,expected",
        [
            (1, ["1 month"]),
            (3, ["3 months"]),
            (12, ["1 year"]),
            (18, ["1 year", "6 months"]),
            (24, ["2 years"]),
        ],
        ids=["one month", "few months", "one year", "year and months", "two years"],
    )
    def test_render(self, months: int, expected: list[str]) -> None:
        """Test that months split into year/month phrases, singular at exactly one."""
        assert month_words(months) == expected


class TestSecondWords:
    @pytest.mark.parametrize(
        "seconds,microseconds,expected",
        [
            (1, 0, ["1 second"]),
            (90, 0, ["1 minute", "30 seconds"]),
            (3_600, 0, ["1 hour"]),
            (86_400, 0, ["1 day"]),
            (90_061, 0, ["1 day", "1 hour", "1 minute", "1 second"]),
            (0, 500_000, ["0.5 seconds"]),
            (0, 0, ["0 seconds"]),
        ],
        ids=["one second", "minute and seconds", "hour", "day", "all units", "sub-second", "zero"],
    )
    def test_render(self, seconds: int, microseconds: int, expected: list[str]) -> None:
        """Test that seconds split into day/hour/minute/second phrases, singular at exactly one."""
        assert second_words(seconds, microseconds) == expected


class TestDecompositionAgreesWithIso:
    """month_words/second_words repeat the divmod split append_month_elems/append_second_elems already do -
    these check the two never drift apart."""

    @pytest.mark.parametrize("months", [1, 6, 12, 18, 30])
    def test_month_words_reports_a_word_per_iso_unit_present(self, months: int) -> None:
        """Test that a "Y"/"M" designator in the ISO fragment corresponds to one word phrase, and vice versa."""
        iso = "".join(append_month_elems([], months))
        assert len(month_words(months)) == iso.count("Y") + iso.count("M")

    @pytest.mark.parametrize("seconds,microseconds", [(1, 0), (90, 0), (90_061, 0), (0, 500_000)])
    def test_second_words_reports_a_word_per_iso_unit_present(self, seconds: int, microseconds: int) -> None:
        """Test that a "D"/"H"/"M"/"S" designator in the ISO fragment corresponds to one word phrase."""
        iso = "".join(append_second_elems(["P"], seconds, microseconds))
        designator_count = sum(iso.count(d) for d in "DHMS")
        assert len(second_words(seconds, microseconds)) == designator_count


class TestJoinWords:
    @pytest.mark.parametrize(
        "words,expected",
        [
            ([], ""),
            (["1 day"], "1 day"),
            (["1 day", "1 hour"], "1 day and 1 hour"),
            (["1 day", "1 hour", "1 minute"], "1 day, 1 hour and 1 minute"),
            (["1 day", "1 hour", "1 minute", "1 second"], "1 day, 1 hour, 1 minute and 1 second"),
        ],
        ids=["empty", "one", "two", "three", "four"],
    )
    def test_render(self, words: list[str], expected: str) -> None:
        """Test the English list join: no separator at one item, "and" before the last item otherwise."""
        assert join_words(words) == expected


class TestFrequencyWord:
    @pytest.mark.parametrize(
        "step,multiplier,expected",
        [
            (Step.SECONDS, 3_600, "Hourly"),
            (Step.SECONDS, 86_400, "Daily"),
            (Step.SECONDS, 604_800, "Weekly"),
            (Step.MONTHS, 1, "Monthly"),
            (Step.MONTHS, 3, "Quarterly"),
            (Step.MONTHS, 12, "Yearly"),
            (Step.SECONDS, 1, None),
            (Step.SECONDS, 60, None),
            (Step.SECONDS, 900, None),
            (Step.MICROSECONDS, 1, None),
        ],
        ids=["hour", "day", "week", "month", "quarter", "year", "second", "minute", "no word", "microseconds"],
    )
    def test_render(self, step: Step, multiplier: int, expected: str | None) -> None:
        """Test that every named frequency resolves and everything else is None."""
        assert frequency_word(step, multiplier) == expected


class TestPeriodName:
    @pytest.mark.parametrize(
        "step,multiplier,month_offset,microsecond_offset,expected",
        [
            (Step.SECONDS, 86_400, 0, 32_400_000_000, "UK Water Day"),
            (Step.MONTHS, 12, 9, 32_400_000_000, "UK Water Year"),
            (Step.SECONDS, 86_400, 0, 0, None),
            (Step.MONTHS, 12, 9, 0, None),
        ],
        ids=["water day", "water year", "unoffset day", "wrong time offset"],
    )
    def test_render(
        self, step: Step, multiplier: int, month_offset: int, microsecond_offset: int, expected: str | None
    ) -> None:
        """Test that only the two recognised grids are named."""
        assert period_name(step, multiplier, month_offset, microsecond_offset) == expected


class TestOriginText:
    @pytest.mark.parametrize(
        "origin,expected",
        [
            (dt.datetime(2024, 1, 1), "2024-01-01"),
            (dt.datetime(1883, 1, 1, 9), "1883-01-01 09:00"),
            (dt.datetime(1883, 1, 1, 9, 30, 15), "1883-01-01 09:30:15"),
            (dt.datetime(1883, 1, 1, 9, 30, 15, 500_000), "1883-01-01 09:30:15.500000"),
        ],
        ids=["midnight", "minutes", "seconds", "microseconds"],
    )
    def test_render(self, origin: dt.datetime, expected: str) -> None:
        """Test that a midnight origin renders as a bare date, and time precision grows only as needed."""
        assert origin_text(origin) == expected
