"""Properties: the basic, immutable, sortable, hashable specification of a Period."""

import datetime as dt
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any

from isoperiod.enums import Step
from isoperiod.exceptions import PeriodValidationError, illegal_step
from isoperiod.iso import (
    append_month_elems,
    append_second_elems,
    microsecond_period_name,
    month_period_name,
    second_period_name,
    second_string,
    tz_label,
)
from isoperiod.words import frequency_word, join_words, month_words, period_name, second_words

if TYPE_CHECKING:
    from isoperiod.parsing import PeriodFields


@dataclass(frozen=True)
class Alignment:
    """How one period's intervals sit inside another's: the result of `Properties._alignment`.

    Attributes:
        aligned: True if every interval of the inner period lies wholly within one interval of the outer,
            never straddling a boundary
        count: The number of inner intervals per outer interval, when that number is the same for every
            interval on the timeline; None when there is no such number
    """

    aligned: bool
    count: int | None


# The two results that carry no count: intervals that do not line up at all, and intervals that line up but
# whose count varies from one to the next (days in a month, which run from 28 to 31).
UNALIGNED = Alignment(aligned=False, count=None)
ALIGNED_VARYING = Alignment(aligned=True, count=None)


@dataclass(eq=True, frozen=True)
class Properties:
    """The complete, validated specification of a period: everything needed to describe one.

    Six fields say all there is to say about a period::

    * (1) `step` and (2) `multiplier` giving its size (e.g. 900 seconds),
    * (3) `month_offset` and (4) `microsecond_offset` defines its interval boundaries,
    * an optional (5) `tzinfo` to describe the time zone,
    * and an (6) `ordinal_shift` choosing which interval is numbered 0.

    Properties objects are immutable and hashable, being a frozen dataclass, and sortable by length - see
    `_order_key`, which the ordering dunders below are built on.

    Why this is separate from Period:
        A Period *does* things with a specification - maps datetimes to ordinals and back, formats, counts. This
        class *is* the specification. Keeping them apart is what lets `parsing` build a period specification out
        of an ISO 8601 string without depending on the Period class hierarchy at all; `periods` then depends on
        both. Folding this into Period would make `parsing` and `periods` import each other.

    This class is internal - `isoperiod` exports only `Period` and the exceptions.
    """

    step: int
    multiplier: int
    month_offset: int
    microsecond_offset: int
    tzinfo: dt.tzinfo | None
    ordinal_shift: int

    @staticmethod
    def of_months(no_of_months: int) -> "Properties":
        """Return a Properties object for an "n"-month period.

        Args:
            no_of_months: The number of months in the period

        Returns:
            A Properties object
        """
        return Properties.of_step_and_multiplier(Step.MONTHS, no_of_months)

    @staticmethod
    def of_seconds(no_of_seconds: int) -> "Properties":
        """Return a Properties object for an "n"-second period.

        Args:
            no_of_seconds: The number of seconds in the period

        Returns:
            A Properties object
        """
        return Properties.of_step_and_multiplier(Step.SECONDS, no_of_seconds)

    @staticmethod
    def of_microseconds(no_of_microseconds: int) -> "Properties":
        """Return a Properties object for an "n"-microsecond period.

        Args:
            no_of_microseconds: The number of microseconds in the period

        Returns:
            A Properties object
        """
        seconds, microseconds = divmod(no_of_microseconds, 1_000_000)
        if microseconds == 0:
            return Properties.of_seconds(seconds)
        return Properties.of_step_and_multiplier(Step.MICROSECONDS, no_of_microseconds)

    @staticmethod
    def of_step_and_multiplier(step: int, multiplier: int) -> "Properties":
        """Return a Properties object representing a period of the given step and multiplier.

        The step represents the basic "unit" of the period and can be one of:
            Step.MICROSECONDS
            Step.SECONDS
            Step.MONTHS

        The multiplier is the number of 'steps' in the period.

        Args:
            step: The step of the period:
            multiplier: The multiplier, or the number of steps
                        in the period

        Examples:
            >>> Properties.of_step_and_multiplier(Step.MONTHS, 12).iso_duration
            'P1Y'
            >>> Properties.of_step_and_multiplier(Step.SECONDS, 24 * 60 * 60).iso_duration
            'P1D'
            >>> Properties.of_step_and_multiplier(Step.SECONDS, 15 * 60).iso_duration
            'PT15M'
            >>> Properties.of_step_and_multiplier(Step.MICROSECONDS, 1_000_000 // 25).iso_duration
            'PT0.04S'

        Returns:
            A Properties object
        """
        return Properties(
            step=step, multiplier=multiplier, month_offset=0, microsecond_offset=0, tzinfo=None, ordinal_shift=0
        )

    def __post_init__(self) -> None:
        """Reject any field combination that could not describe a real period.

        This runs on every construction, including the copies made by `dataclasses.replace`, and it is what
        lets the rest of the package take a Properties at face value rather than re-checking it. Five rules
        are enforced:

        * `step` must be one of the three Step members.
        * `multiplier` must be positive - a period has to have a length.
        * `month_offset` and `microsecond_offset` must be zero or positive; a period is shifted forwards, and
          a backwards shift is expressed as the equivalent forward one.
        * `month_offset` must be zero unless the step is MONTHS, since a period of fixed-length units cannot
          be offset by a variable-length month.

        `tzinfo` and `ordinal_shift` are unconstrained: any tzinfo is legal, as is any integer shift.

        Note that this checks legality, not canonical form - an offset larger than the period itself is legal
        here and reduced separately by `normalise_offsets`.

        Raises:
            PeriodValidationError: If any of the above rules is broken
        """
        if self.step not in Step:
            raise illegal_step(self.step)

        if self.multiplier <= 0:
            raise PeriodValidationError(f"Illegal multiplier: {self.multiplier}. Must be greater than zero.")

        if self.month_offset < 0:
            raise PeriodValidationError(f"Illegal month offset: {self.month_offset}. Must be zero or greater.")

        if self.microsecond_offset < 0:
            raise PeriodValidationError(
                f"Illegal microsecond offset: {self.microsecond_offset}. Must be zero or greater."
            )

        if (self.step != Step.MONTHS) and (self.month_offset != 0):
            raise PeriodValidationError(
                f"Illegal month offset '{self.month_offset}' for non-month step '{self.step}'. "
                f"Month offset must be zero."
            )

    def normalise_offsets(self) -> "Properties":
        """Return an equivalent Properties object with the offset reduced to less than one period.

        Shifting a period by a whole multiple of its own length splits the timeline exactly as leaving it
        alone does, so only the remainder matters. This reduces the offset modulo the period's length,
        giving one canonical form per way of splitting the timeline - which is what makes equal Properties
        compare equal.

        Whichever offset field the step uses is taken modulo the multiplier, expressed in that step's unit:
        `month_offset` for MONTHS, `microsecond_offset` for SECONDS (against `multiplier * 1_000_000`) and
        for MICROSECONDS.

        Any `ordinal_shift` is also cleared, since moving the interval boundaries invalidates the numbering
        it established. `self` is returned unchanged only when there was nothing to reduce and no shift.

        Returns:
            A Properties object

        Raises:
            PeriodValidationError: If a non-month step carries a month offset

        Examples:
            A 13-month offset on a one-year period reduces to one month, since 13 % 12 == 1.

            >>> Properties.of_months(12).with_month_offset(13).month_offset
            1

            A 25-second offset on a ten-second period reduces to five, and a 30-second one to none at all.

            >>> Properties.of_seconds(10).with_microsecond_offset(25_000_000).microsecond_offset
            5000000
            >>> Properties.of_seconds(10).with_microsecond_offset(30_000_000).microsecond_offset
            0
        """
        new_month_offset: int = self.month_offset
        new_microsecond_offset: int = self.microsecond_offset
        if self.step == Step.MONTHS:
            new_month_offset = self.month_offset % self.multiplier

        elif self.step == Step.SECONDS:
            if self.month_offset != 0:
                raise PeriodValidationError(
                    f"Illegal month offset '{self.month_offset}' for non-month step '{self.step}'. "
                    f"Month offset must be zero."
                )
            new_microsecond_offset = self.microsecond_offset % (self.multiplier * 1_000_000)

        elif self.step == Step.MICROSECONDS:
            if self.month_offset != 0:
                raise PeriodValidationError(
                    f"Illegal month offset '{self.month_offset}' for non-month step '{self.step}'. "
                    f"Month offset must be zero."
                )
            new_microsecond_offset = self.microsecond_offset % self.multiplier

        else:
            raise illegal_step(self.step)

        if (
            (new_month_offset == self.month_offset)
            and (new_microsecond_offset == self.microsecond_offset)
            and (self.ordinal_shift == 0)
        ):
            return self

        return replace(self, month_offset=new_month_offset, microsecond_offset=new_microsecond_offset, ordinal_shift=0)

    def with_month_offset(self, month_amount: int) -> "Properties":
        """Return a Properties object derived from this one with the given month_offset.

        Args:
            month_amount: The amount to add to the month_offset

        Returns:
            A Properties object
        """
        return replace(self, month_offset=self.month_offset + month_amount, ordinal_shift=0).normalise_offsets()

    def with_microsecond_offset(self, microsecond_amount: int) -> "Properties":
        """Return a Properties object derived from this one with the given microsecond_offset.

        Args:
            microsecond_amount: The amount to add to the microsecond_offset

        Returns:
            A Properties object
        """
        return replace(
            self, microsecond_offset=self.microsecond_offset + microsecond_amount, ordinal_shift=0
        ).normalise_offsets()

    def with_tzinfo(self, tzinfo: dt.tzinfo | None) -> "Properties":
        """Return a Properties object derived from this one with  the given datetime tzinfo object (time zone).

        Args:
            tzinfo: The tzinfo object (or None) of the new Properties

        Returns:
            A Properties object
        """
        return replace(self, tzinfo=tzinfo)

    def with_ordinal_shift(self, ordinal_shift: int) -> "Properties":
        """Return a Properties object derived from this one with the given ordinal shift value.

        Args:
            ordinal_shift: The amount by which ordinal values are shifted in a Period object created from the new
                           Properties object

        Returns:
            A Properties object
        """
        return replace(self, ordinal_shift=ordinal_shift)

    def with_offset_period_fields(self, offset_period_fields: "PeriodFields") -> "Properties":
        """Return a Properties object derived from this one with new month and microsecond offsets.

        Args:
            offset_period_fields: A PeriodFields object that is used to calculate the month and microsecond offsets

        Returns:
            A Properties object
        """
        months_seconds = offset_period_fields.get_months_seconds()
        return replace(
            self,
            month_offset=months_seconds.months,
            microsecond_offset=months_seconds.total_microseconds(),
            ordinal_shift=0,
        ).normalise_offsets()

    @property
    def iso_duration(self) -> str:
        """The ISO 8601 duration string of the period defined by this Properties object.

        Returns:
            The ISO 8601 duration string of this period
        """
        match self.step:
            case Step.MICROSECONDS:
                return microsecond_period_name(self.multiplier)
            case Step.SECONDS:
                return second_period_name(self.multiplier)
            case Step.MONTHS:
                return month_period_name(self.multiplier)
        raise illegal_step(self.step)

    @property
    def timedelta(self) -> dt.timedelta | None:
        """The timedelta matching this period's duration, or None if it has no fixed length.

        Backs :attr:`isoperiod.Period.timedelta`; see there for details.

        Returns:
            A timedelta object, or None
        """
        match self.step:
            case Step.MICROSECONDS:
                seconds, microseconds = divmod(self.multiplier, 1_000_000)
                return dt.timedelta(seconds=seconds, microseconds=microseconds)
            case Step.SECONDS:
                return dt.timedelta(seconds=self.multiplier)
            case Step.MONTHS:
                return None
        raise illegal_step(self.step)

    def _append_step_elems(self, elems: list[str]) -> None:
        """Add the elements describing the step and multiplier to a list of strings.

        Joined together, the list forms an ISO 8601 duration string.

        Args:
            elems: The list of strings used to calculate the repr string
        """
        match self.step:
            case Step.MICROSECONDS:
                seconds, microseconds = divmod(self.multiplier, 1_000_000)
                append_second_elems(elems, seconds, microseconds)
            case Step.SECONDS:
                append_second_elems(elems, self.multiplier, 0)
            case Step.MONTHS:
                append_month_elems(elems, self.multiplier)
            case _:
                raise illegal_step(self.step)

    def _append_offset_elems(self, elems: list[str]) -> None:
        """Add the elements describing the month and microsecond offsets to a list of strings.

        Joined together, the list forms the "+offset" part, in a style similar to an ISO 8601 duration.

        Args:
            elems: The list of strings used to calculate the repr string
        """
        if (self.month_offset == 0) and (self.microsecond_offset == 0):
            return
        elems.append("+")
        if self.month_offset > 0:
            append_month_elems(elems, self.month_offset)
        if self.microsecond_offset > 0:
            seconds, microseconds = divmod(self.microsecond_offset, 1_000_000)
            append_second_elems(elems, seconds, microseconds)
        return

    def _append_tz_elems(self, elems: list[str]) -> None:
        """Add elements to a list of string that describe the tzinfo object.

        Args:
            elems: The list of strings used to calculate the repr string
        """
        if self.tzinfo is not None:
            elems.append(f"[{tz_label(self.tzinfo)}]")

    def _append_shift_elems(self, elems: list[str]) -> None:
        """Add the elements describing the ordinal shift to a list of strings.

        Args:
            elems: The list of strings used to calculate the repr string
        """
        if self.ordinal_shift != 0:
            elems.append(f"@{self.ordinal_shift}")

    @property
    def pl_interval(self) -> str:
        """The step and multiplier as a Polars duration string.

        Backs :attr:`isoperiod.Period.pl_interval`; see there for the Polars methods that accept it.

        Returns:
            A string suitable for use with Polars methods
        """
        match self.step:
            case Step.MICROSECONDS:
                return f"{self.multiplier}us"
            case Step.SECONDS:
                return f"{self.multiplier}s"
            case Step.MONTHS:
                return f"{self.multiplier}mo"
            case _:
                raise illegal_step(self.step)

    @property
    def pl_offset(self) -> str:
        """The month and microsecond offsets as a Polars duration string.

        Backs :attr:`isoperiod.Period.pl_offset`; see there for the Polars methods that accept it.

        Returns:
            A string suitable for use with Polars methods
        """
        return f"{self.month_offset}mo{self.microsecond_offset}us"

    @property
    def offset(self) -> str:
        """The month and microsecond offsets, as the "+offset" part of a Period.of_duration string.

        Backs :attr:`isoperiod.Period.offset`; see there for details.

        Returns:
            A string suitable for use as the offset part of a Period.of_duration string
        """
        month_part = f"{self.month_offset}M" if self.month_offset > 0 else ""
        microsecond_part = ""
        if self.microsecond_offset > 0:
            seconds, microseconds = divmod(self.microsecond_offset, 1_000_000)
            microsecond_part = f"T{second_string(seconds, microseconds)}S"
        offset_str = f"+{month_part}{microsecond_part}" if month_part or microsecond_part else ""

        return offset_str

    def duration_words(self) -> list[str]:
        """Return this period's duration (excluding any offset) as a list of English word phrases.

        Returns:
            A list of phrases such as ``["1 year", "6 months"]``
        """
        match self.step:
            case Step.MICROSECONDS:
                seconds, microseconds = divmod(self.multiplier, 1_000_000)
                return second_words(seconds, microseconds)
            case Step.SECONDS:
                return second_words(self.multiplier, 0)
            case Step.MONTHS:
                return month_words(self.multiplier)
        raise illegal_step(self.step)

    def offset_suffix(self) -> str:
        """Return this period's offset as a bracketed suffix, or "" if it has none.

        Returns:
            A string such as ``" (+9 months and 9 hours)"``, or ``""``
        """
        if (self.month_offset == 0) and (self.microsecond_offset == 0):
            return ""
        words = month_words(self.month_offset) if self.month_offset > 0 else []
        if self.microsecond_offset > 0:
            seconds, microseconds = divmod(self.microsecond_offset, 1_000_000)
            words += second_words(seconds, microseconds)
        return f" (+{join_words(words)})"

    @property
    def verbose(self) -> str:
        """This period's duration and offset, spelled out in English words.

        Backs :attr:`isoperiod.Period.verbose`; see there for details.

        Returns:
            A string such as "1 year (+9 months and 9 hours)"

        Examples:
            >>> Properties.of_months(12).verbose
            '1 year'
            >>> Properties.of_seconds(86_400).with_microsecond_offset(32_400_000_000).verbose
            '1 day (+9 hours)'
        """
        return join_words(self.duration_words()) + self.offset_suffix()

    @property
    def descriptive(self) -> str:
        """This period's frequency, named where there is a common word for it.

        Backs :attr:`isoperiod.Period.descriptive`; see there for details.

        Returns:
            A string such as "Daily" or "15 minutes", with a name or offset in brackets if there is one

        Examples:
            >>> Properties.of_seconds(86_400).descriptive
            'Daily'
            >>> Properties.of_seconds(900).descriptive
            '15 minutes'
        """
        word = frequency_word(self.step, self.multiplier)
        base = word if word is not None else join_words(self.duration_words())
        name = period_name(self.step, self.multiplier, self.month_offset, self.microsecond_offset)
        if name is not None:
            return f"{base} ({name})"
        return base + self.offset_suffix()

    def is_epoch_agnostic(self) -> bool:
        """Return True if this period splits the timeline the same way whatever epoch is used.

        Backs :meth:`isoperiod.Period.is_epoch_agnostic`; see there for what that means, and why P1D is
        epoch agnostic but P7D is not.

        Returns:
            True if the split is independent of the epoch, False otherwise
        """
        # A period is epoch agnostic iff its multiplier divides evenly into the fixed
        # unit above it: seconds into a day, months into a year. Microseconds periods
        # are additionally capped at one second - a microsecond period spanning more
        # than a second is never considered epoch agnostic, even if its multiplier
        # would otherwise divide evenly into a day (e.g. PT1.5S measured as 1_500_000
        # microseconds: 86_400_000_000 % 1_500_000 == 0, but this is still not agnostic).
        match self.step:
            case Step.MICROSECONDS:
                if self.multiplier > 1_000_000:
                    return False
                divisor = 86_400_000_000
            case Step.SECONDS:
                divisor = 86_400
            case Step.MONTHS:
                divisor = 12
            case _:
                raise illegal_step(self.step)
        return divisor % self.multiplier == 0

    def _microsecond_multiplier(self) -> int:
        """Return this period's multiplier expressed in microseconds.

        Only meaningful for a MICROSECONDS or SECONDS step; a MONTHS period has no fixed length in microseconds, so
        callers must exclude that case first.

        Returns:
            The multiplier, in microseconds
        """
        return self.multiplier if self.step == Step.MICROSECONDS else self.multiplier * 1_000_000

    def count(self, other: "Properties") -> int | None:
        """Return the number of intervals of this period per interval of `other`, or None if there is no
        constant number.

        Backs :meth:`isoperiod.Period.count`; see there for details.

        Args:
            other: The period whose intervals this period's intervals are counted within

        Returns:
            The constant number of intervals per interval of `other`, or None
        """
        return self._alignment(other).count

    def is_subperiod_of(self, other: "Properties") -> bool:
        """Return True if every interval of this period falls entirely inside a single interval of `other`.

        Backs :meth:`isoperiod.Period.is_subperiod_of`; see there for details.

        Args:
            other: The period whose intervals must contain this period's

        Returns:
            True if every interval of this period lies within one interval of `other`, False otherwise
        """
        return self._alignment(other).aligned

    def _alignment(self, other: "Properties") -> Alignment:
        """Return how this period's intervals sit inside `other`'s.

        The single calculation that both :meth:`count` and :meth:`is_subperiod_of` read from, since the two
        facts - whether the boundaries line up, and how many intervals fit - are worked out together. Each
        public method returns one field of the result.

        Args:
            other: The period whose intervals this period's intervals are counted within

        Returns:
            An Alignment: aligned, plus the constant count if there is one
        """
        # Periods over different timezones are not aligned
        if self.tzinfo != other.tzinfo:
            return UNALIGNED

        # The same period fits itself exactly once.
        # The ordinal_shift can be ignored as it does not affect how the timeline is split.
        if (
            (self.step == other.step)
            and (self.multiplier == other.multiplier)
            and (self.month_offset == other.month_offset)
            and (self.microsecond_offset == other.microsecond_offset)
        ):
            return Alignment(aligned=True, count=1)

        if self.step == Step.MONTHS:
            if other.step != Step.MONTHS:
                # A month period can never fit evenly within a smaller, fixed-length period.
                return UNALIGNED
            count = self._divisible_count(self.multiplier, other.multiplier, self.month_offset, other.month_offset)
            if (count is None) or (self.microsecond_offset != other.microsecond_offset):
                return UNALIGNED
            return Alignment(aligned=True, count=count)

        # From here, self.step is Step.MICROSECONDS or Step.SECONDS.
        self_us = self._microsecond_multiplier()

        if other.step == Step.MONTHS:
            # Months have variable length, so there is never a constant count; the day
            # is the largest unit common to every month, so only alignment (not a
            # count) can be determined here.
            # math.gcd(28, 29, 30, 31) == 1, so it's enough to check that self aligns
            # to a day; other.month_offset can be ignored, as a whole number of months
            # shifts a boundary by a whole number of days.
            # Microseconds are the shared unit: offsets are always held in microseconds,
            # so the multipliers must be too.
            day_in_microseconds = 86_400_000_000
            count = self._divisible_count(
                self_us, day_in_microseconds, self.microsecond_offset, other.microsecond_offset
            )
            return UNALIGNED if count is None else ALIGNED_VARYING

        if (self.step == Step.SECONDS) and (other.step == Step.MICROSECONDS):
            # A second period can never fit evenly within a (necessarily sub-second)
            # microsecond period.
            return UNALIGNED

        other_us = other._microsecond_multiplier()
        count = self._divisible_count(self_us, other_us, self.microsecond_offset, other.microsecond_offset)
        return UNALIGNED if count is None else Alignment(aligned=True, count=count)

    @staticmethod
    def _divisible_count(
        self_multiplier: int, other_multiplier: int, self_offset: int, other_offset: int
    ) -> int | None:
        """Count how many "self" intervals fit in one "other" interval, or None if they do not line up.

        Both periods must already be expressed in the same base unit - both in microseconds, or both in months.

        Two periods line up when both of these hold:

        * `other` is a whole multiple of `self`, so a whole number of them fits. That multiple is the count.
        * Their offsets differ by a whole number of `self` periods, so every boundary of `other` lands on a
          boundary of `self`. Note it is the *difference* that matters, not the offsets being equal - a 15-minute
          period offset by 5 minutes has boundaries at :05, :20, :35 and :50, so it lines up with an hourly period
          offset by any of those.

        Args:
            self_multiplier: The "self" period's length, in the shared unit
            other_multiplier: The "other" period's length, in the shared unit
            self_offset: The "self" period's offset, in the shared unit
            other_offset: The "other" period's offset, in the shared unit

        Returns:
            The number of "self" intervals per "other" interval, or None if they do not line up

        Examples:
            Working in minutes for legibility (the real callers pass microseconds or months):

            Four 15-minute intervals per hour, both on the natural boundaries.

            >>> Properties._divisible_count(15, 60, 0, 0)
            4

            Same, with both offset alike: :05 :20 :35 :50 inside :05 -> :05.

            >>> Properties._divisible_count(15, 60, 5, 5)
            4

            Offsets differ by 15 minutes - one whole "self" period - so they still line up: the boundaries at
            :05 :20 :35 :50 include :20, where "other" starts.

            >>> Properties._divisible_count(15, 60, 5, 20)
            4

            An hour is not a whole multiple of 25 minutes.

            >>> print(Properties._divisible_count(25, 60, 0, 0))
            None

            Offsets differ by 7 minutes, which is not a whole number of 15-minute periods, so "other" starts
            part-way through one of "self"'s intervals.

            >>> print(Properties._divisible_count(15, 60, 5, 12))
            None
        """
        mult_q, mult_r = divmod(other_multiplier, self_multiplier)
        if mult_r != 0:
            return None
        if (other_offset - self_offset) % self_multiplier != 0:
            return None
        return mult_q

    def _nominal_microseconds(self) -> int:
        """Return this period's length in microseconds, taking a month to be its mean Gregorian length.

        A calendar month has no fixed length, so for a MONTHS step this is an approximation. It exists solely to
        put periods in "shortest first" order, which needs calendar and fixed-length periods to be comparable
        against each other. Nothing else uses it: alignment, counting and every interval calculation work off the
        real calendar, and :attr:`timedelta` still returns None for a month rather than an approximation.

        Contrast :meth:`_microsecond_multiplier`, which is exact but undefined for a MONTHS step.

        Returns:
            The period's nominal length, in microseconds

        Raises:
            PeriodValidationError: If the step is not one of the three legal steps
        """
        # The mean length of a Gregorian calendar month, in microseconds: a year of 365.2425 days divided by 12
        nominal_month_microseconds = (365.2425 / 12) * 24 * 60 * 60 * 1_000_000

        match self.step:
            case Step.MICROSECONDS:
                return self.multiplier
            case Step.SECONDS:
                return self.multiplier * 1_000_000
            case Step.MONTHS:
                return int(self.multiplier * nominal_month_microseconds)
            case _:
                raise illegal_step(self.step)

    def _order_key(self) -> tuple[int, int, int, int, dt.tzinfo | None, int]:
        """Return the tuple that orders this period against another: nominal length first, then enough of the
        remaining fields to break every tie.

        Length is what the ordering is *for*, so it leads. Everything after it only separates periods of equal
        nominal length, and does so arbitrarily but consistently; what matters is that the order is total and
        agrees with `__eq__`. It does, because `step` together with the nominal length recovers `multiplier`, so
        no two unequal Properties can share a key.

        `tzinfo` is carried raw rather than reduced to something orderable, so that comparing two periods alike
        in every respect but their timezone raises TypeError, as comparing a naive datetime against an aware one
        does. Tuple comparison stops at the first field that settles the order, so the timezones of periods of
        differing length are never compared at all.

        Returns:
            A tuple that orders this period against another
        """
        return (
            self._nominal_microseconds(),
            self.step,
            self.month_offset,
            self.microsecond_offset,
            self.tzinfo,
            self.ordinal_shift,
        )

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Properties):
            return NotImplemented
        return self._order_key() < other._order_key()

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, Properties):
            return NotImplemented
        return self._order_key() <= other._order_key()

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, Properties):
            return NotImplemented
        return self._order_key() > other._order_key()

    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, Properties):
            return NotImplemented
        return self._order_key() >= other._order_key()

    def __str__(self) -> str:
        elems: list[str] = ["P"]
        self._append_step_elems(elems)
        self._append_offset_elems(elems)
        return "".join(elems)

    def __repr__(self) -> str:
        elems: list[str] = ["P"]
        self._append_step_elems(elems)
        self._append_offset_elems(elems)
        self._append_tz_elems(elems)
        self._append_shift_elems(elems)
        return "".join(elems)
