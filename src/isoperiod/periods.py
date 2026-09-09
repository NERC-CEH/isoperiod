"""The Period class: the abstract Period base class, its concrete implementations, and the factory
functions that choose the right implementation for a given Properties object.
"""

import datetime as dt
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import replace
from typing import Any, ClassVar, override

from isoperiod import parsing, timeline
from isoperiod.enums import Step
from isoperiod.exceptions import PeriodParsingError, PeriodValidationError, illegal_step
from isoperiod.iso import tz_label
from isoperiod.properties import Properties
from isoperiod.timeline import (
    gregorian_seconds,
    month_ordinal,
    month_shift,
    naive,
    total_microseconds,
    year_month,
)
from isoperiod.words import frequency_word, join_words, origin_text


class Period(ABC):
    """A repeating period of time, which splits the Gregorian timeline into consecutive, numbered intervals.

    A Period divides all of time into intervals of one fixed size - every hour, every 15 minutes, every month -
    and numbers each interval with an integer "ordinal". Two methods map between the two views:

    ``ordinal(datetime) -> int``
        The ordinal of the interval containing that datetime.
    ``datetime(ordinal) -> datetime``
        The first instant of that interval.

    They are inverses, in the sense that ``period.ordinal(d) == n`` for every datetime where
    ``period.datetime(n) <= d < period.datetime(n + 1)``.

    An **offset** shifts every one of those boundaries by a fixed amount, so intervals keep their size but start
    somewhere else - e.g. a hydrological day running 09:00 to 09:00, or a year starting in October. In string form it
    is written ``<duration>+<offset>`` (``"P1D+T9H"``), this package's own extension of the ISO 8601 duration
    format. See :doc:`/user_guide/offsets`.

    Period is abstract: build one with an ``of_*`` factory, then refine it with the ``with_*`` methods, each of
    which returns a new Period rather than mutating the original.

    Instances are immutable and hashable, so they work in sets and as dict keys. They sort shortest first, with a
    calendar month taken as its mean Gregorian length so that calendar and fixed-length periods order against one
    another; comparing two Periods that differ only in their tzinfo raises ``TypeError``, just as comparing a
    naive datetime with an aware one does.

    Examples:
        >>> from datetime import datetime, timedelta
        >>> from isoperiod import Period

        Which hour is 09:47 in, and when did that hour start and end?

        >>> pt1h = Period.of_hours(1)
        >>> d = datetime(2024, 3, 1, 9, 47)
        >>> n = pt1h.ordinal(d)
        >>> pt1h.datetime(n)
        datetime.datetime(2024, 3, 1, 9, 0)
        >>> pt1h.datetime(n + 1)
        datetime.datetime(2024, 3, 1, 10, 0)

        Ordinals are consecutive integers, so interval arithmetic is integer arithmetic.

        >>> pt1h.ordinal(d + timedelta(days=1)) - pt1h.ordinal(d)
        24

        Months work the same way, despite their varying length.

        >>> Period.of_months(1).floor(datetime(2024, 3, 15))
        datetime.datetime(2024, 3, 1, 0, 0)

        An offset moves every boundary: a day running 09:00 -> 09:00.

        >>> water_day = Period.of_days(1).with_hour_offset(9)
        >>> water_day.floor(datetime(2024, 3, 15, 7, 30))
        datetime.datetime(2024, 3, 14, 9, 0)
    """

    @staticmethod
    def of(period_string: str) -> "Period":
        """Return a Period from the supplied string.

        Tries each supported string format in turn (plain ISO 8601 duration, the extended "+offset" form, and
        "<start>/<duration>") and returns the first that matches.

        Args:
            period_string: A string containing a period
                           definition

        Returns:
            A Period object defined by the supplied string

        Raises:
            PeriodParsingError: If the string does not match any supported period format.
        """
        properties = parsing.parse_iso_duration(period_string)
        if properties is not None:
            return build_base_period(properties)
        properties = parsing.parse_period_offset(period_string)
        if properties is not None:
            return build_offset_period(properties)
        result = parsing.parse_date_and_duration(period_string)
        if result is not None:
            properties, origin = result
            return build_shifted_period(properties).with_origin(origin)
        raise PeriodParsingError(f"Illegal period: {period_string}")

    @staticmethod
    def of_iso_duration(iso_8601_duration: str) -> "Period":
        """Return a Period from a strict ISO 8601 duration string

        Args:
            iso_8601_duration: An ISO 8601 duration string such as "P1Y" or "PT15M". Does not accept "+offset" format.

        Returns:
            A Period object defined by the supplied ISO 8601 duration string

        Raises:
            PeriodParsingError: If the string does not contain a valid ISO 8601 duration value.
        """
        properties = parsing.parse_iso_duration(iso_8601_duration)
        if properties is None:
            raise PeriodParsingError(f"Illegal ISO 8601 duration: {iso_8601_duration}")
        return build_base_period(properties)

    @staticmethod
    def of_duration(duration: str) -> "Period":
        """Return a Period from an (extended) ISO 8601 duration string

        Both plain and extended ("+offset") ISO 8601 duration strings are supported; the extended form is tried first.

        Args:
            duration: An ISO 8601 duration string e.g. "P1Y" or "PT15M", or with offset e.g. "P1D+T9H"

        Returns:
            A Period object defined by the supplied (extended) ISO 8601 duration string

        Raises:
            PeriodParsingError: If the string does not contain a valid (extended) ISO 8601 duration value.
        """
        properties = parsing.parse_period_offset(duration)
        if properties is not None:
            return build_offset_period(properties)
        properties = parsing.parse_iso_duration(duration)
        if properties is not None:
            return build_base_period(properties)
        raise PeriodParsingError(f"Illegal duration: {duration}")

    @staticmethod
    def of_date_and_duration(date_duration: str) -> "Period":
        """Return a Period from date/duration string.

        The Period's timeline origin is set to the given date, and period steps built as normal from that origin.

        Args:
            date_duration: An ISO 8601 duration string of the form <start>/<duration>, e.g. "2024-01-01/P1D"

        Returns:
            A Period object defined by the supplied ISO 8601 duration string

        Raises:
            PeriodParsingError: If the string does not contain a valid ``<start>/<duration>`` value.
        """
        result = parsing.parse_date_and_duration(date_duration)
        if result is None:
            raise PeriodParsingError(f"Illegal date/duration string: {date_duration}")
        properties, origin = result
        return build_shifted_period(properties).with_origin(origin)

    @staticmethod
    def of_years(no_of_years: int) -> "Period":
        """Return a Period of `no_of_years` calendar years, each starting on January 1st."""
        return build_base_period(Properties.of_months(no_of_years * 12))

    @staticmethod
    def of_months(no_of_months: int) -> "Period":
        """Return a Period of `no_of_months` calendar months, each starting on the 1st."""
        return build_base_period(Properties.of_months(no_of_months))

    @staticmethod
    def of_days(no_of_days: int) -> "Period":
        """Return a Period of `no_of_days` days, each starting at midnight."""
        return build_base_period(Properties.of_seconds(no_of_days * 86_400))

    @staticmethod
    def of_hours(no_of_hours: int) -> "Period":
        """Return a Period of `no_of_hours` hours, each starting on the hour."""
        return build_base_period(Properties.of_seconds(no_of_hours * 3_600))

    @staticmethod
    def of_minutes(no_of_minutes: int) -> "Period":
        """Return a Period of `no_of_minutes` minutes, each starting on the minute."""
        return build_base_period(Properties.of_seconds(no_of_minutes * 60))

    @staticmethod
    def of_seconds(no_of_seconds: int) -> "Period":
        """Return a Period of `no_of_seconds` whole seconds."""
        return build_base_period(Properties.of_seconds(no_of_seconds))

    @staticmethod
    def of_microseconds(no_of_microseconds: int) -> "Period":
        """Return a Period of `no_of_microseconds` microseconds, the finest resolution a Period can have."""
        return build_base_period(Properties.of_microseconds(no_of_microseconds))

    @staticmethod
    def of_timedelta(timedelta: dt.timedelta) -> "Period":
        """Return a Period matching the duration of `timedelta`."""
        return build_base_period(Properties.of_microseconds(total_microseconds(timedelta)))

    def __init__(self, properties: Properties) -> None:
        self._properties = properties

    @property
    def iso_duration(self) -> str:
        """The standard ISO 8601 duration string of this period"""
        return self._properties.iso_duration

    @property
    def tzinfo(self) -> dt.tzinfo | None:
        """Get the tzinfo property"""
        return self._properties.tzinfo

    @property
    def min_ordinal(self) -> int:
        """Get the minimum valid ordinal of this Period.

        This is defined as the minimum ordinal value that you can pass to the datetime method and have Python not
        throw an error because the datetime is out of bounds (e.g. prior to year 0 or after year 9999)

        Returns:
            The minimum ordinal value of this Period
        """
        min_ordinal: int
        try:
            min_ordinal = self.ordinal(dt.datetime.min)
        except (ValueError, OverflowError):
            min_ordinal = self.without_offset().ordinal(dt.datetime.min)
        try:
            self.datetime(min_ordinal)
        except (ValueError, OverflowError):
            min_ordinal += 1
        return min_ordinal

    @property
    def max_ordinal(self) -> int:
        """Get the maximum valid ordinal

        This is defined as the maximum ordinal value that you can pass to the datetime method and have Python not
        throw an error because the datetime is out of bounds (e.g. prior to year 0 or after year 9999)

        Returns:
            The maximum ordinal value of this Period
        """
        return self.ordinal(dt.datetime.max)

    @property
    def timedelta(self) -> dt.timedelta | None:
        """A timedelta object that matches the duration of this period, or None if no such timedelta exists

        There is no timedelta for monthly or yearly periods, as these are not of a fixed length.

        Returns:
            A timedelta object, or None
        """
        return self._properties.timedelta

    @property
    def pl_interval(self) -> str:
        """A string that captures the step and multiplier of this period and which is suitable for use with Polars.

        The returned string is defined using the Polars duration string language, and can be used in
        Polars methods such as :

            polars.DataFrame.group_by_dynamic(..., every=period.pl_interval, ...)

            polars.datetime_ranges(..., interval=period.pl_interval, ...)

        Returns:
            A string suitable for use with Polars methods
        """
        return self._properties.pl_interval

    @property
    def pl_offset(self) -> str:
        """A string that captures the month and microsecond offsets of this period and which is suitable for use with
        Polars.

        The returned string is defined using the Polars duration string language, and can be used in
        Polars methods such as:

            polars.Expr.dt.offset_by(by=period.pl_offset)

        Returns:
            A string suitable for use with Polars methods
        """
        return self._properties.pl_offset

    @property
    def offset(self) -> str:
        """Return a string that captures the month and microsecond offsets of this period which conforms to the offset
        bit of the string required in a Period.of_duration string.

        Returns:
            A string suitable for use with Period of_duration string
        """
        return self._properties.offset

    @property
    def month_offset(self) -> int:
        """The month offset of this period

        Returns:
            An integer representing the month offset
        """
        return self._properties.month_offset

    @property
    def microsecond_offset(self) -> int:
        """The microsecond offset of this period

        Returns:
            An integer representing the microsecond offset
        """
        return self._properties.microsecond_offset

    @property
    def verbose(self) -> str:
        """This period's duration, offset and origin, spelled out in English words.

        For display only - not accepted by :meth:`of` or any other constructor. See :attr:`iso_duration` and
        :meth:`__str__` for the parseable forms.

        Returns:
            A string such as "1 year (+9 months and 9 hours)"

        Examples:
            >>> Period.of_years(1).verbose
            '1 year'
            >>> Period.of("P1D+T9H").verbose
            '1 day (+9 hours)'
            >>> Period.of("2024-01-01/P7D").verbose
            '7 days (from 2024-01-01)'
        """
        origin = self._origin_datetime()
        if origin is None:
            return self._properties.verbose
        return f"{join_words(self._properties.duration_words())} (from {origin_text(origin)})"

    @property
    def descriptive(self) -> str:
        """This period's frequency, named where there is a common word or recognised name for it.

        For display only - see :attr:`verbose` for the same caveat.

        Returns:
            A string such as "Daily" or "15 minutes", with a name, offset or origin in brackets if there is one

        Examples:
            >>> Period.of_days(1).descriptive
            'Daily'
            >>> Period.of("P1D+T9H").descriptive
            'Daily (UK Water Day)'
            >>> Period.of("2024-01-01/P7D").descriptive
            'Weekly (from 2024-01-01)'
        """
        origin = self._origin_datetime()
        if origin is None:
            return self._properties.descriptive
        base = frequency_word(self._properties.step, self._properties.multiplier)
        base = base if base is not None else join_words(self._properties.duration_words())
        return f"{base} (from {origin_text(origin)})"

    def has_offset(self) -> bool:
        """Check if this period has an offset

        Returns:
            True if has offset, False if not
        """
        return self.month_offset > 0 or self.microsecond_offset > 0

    def is_epoch_agnostic(self) -> bool:
        """Return True if the way that this period splits the timeline does not depend on the epoch used to perform
        calculations.

        This method assumes that the epoch will always be midnight at the start of the first day of a year.

        Most commonly used periods such as P1Y, P1M, P1D, PT15M and so on are epoch agnostic.

        A period such as P7D is not epoch agnostic however. The calculation will typically be done using modulus
        arithmetic on the number of days since the epoch, and this will split the timeline into different 7-day
        intervals depending on the epoch.

        Returns:
            True if this period splits the timeline into the same intervals regardless of the epoch, False
            otherwise.
        """
        return self._properties.is_epoch_agnostic()

    @abstractmethod
    def ordinal(self, datetime_obj: dt.datetime) -> int:
        """Return the ordinal of the interval that contains the supplied datetime.

        The ordinal identifies one interval on this period's timeline: the one that starts at or before
        `datetime_obj` and ends before the next begins. Ordinals are consecutive integers, so the interval
        following ordinal ``n`` is always ``n + 1``.

        Args:
            datetime_obj: The datetime whose interval is wanted. Any tzinfo it carries is ignored.

        Returns:
            An integer ordinal value

        Raises:
            OverflowError: If this period's offset shifts the calculation outside the datetime range. Only
                reachable for a period with an offset, at the very start of the timeline.

        Examples:
            >>> from datetime import datetime

            Every datetime in March 2024 shares one ordinal ...

            >>> p1m = Period.of_months(1)
            >>> d = datetime(2024, 3, 15, 9, 47)
            >>> n = p1m.ordinal(d)
            >>> n == p1m.ordinal(datetime(2024, 3, 1)) == p1m.ordinal(datetime(2024, 3, 31, 23, 59))
            True

            ... which Period.datetime() turns back into the start of that month.

            >>> p1m.datetime(n)
            datetime.datetime(2024, 3, 1, 0, 0)
            >>> p1m.datetime(n) <= d < p1m.datetime(n + 1)
            True

        Note:
            An ordinal only means anything to the Period that produced it. Each period numbers the timeline in
            its own units, and feeding one period's ordinal to another's :meth:`datetime` gives a wrong answer
            rather than an error:

            >>> from datetime import datetime
            >>> n = Period.of_months(1).ordinal(datetime(2024, 3, 15))
            >>> n
            24290
            >>> Period.of_days(1).datetime(n)
            datetime.datetime(67, 7, 3, 0, 0)
        """

    @abstractmethod
    def datetime(self, ordinal: int) -> dt.datetime:
        """Return the datetime at which the interval with the supplied ordinal starts.

        The inverse of :meth:`ordinal`.

        Args:
            ordinal: The integer ordinal, as produced by this same Period's :meth:`ordinal`

        Returns:
            A datetime object marking the first instant of that interval, carrying this Period's own tzinfo

        Raises:
            ValueError: If the ordinal maps outside the year range 0001-9999. Ordinals are unbounded integers
                but datetimes are not, so the extremes of the timeline are unreachable.

        Examples:
            >>> from datetime import datetime
            >>> pt1h = Period.of_hours(1)
            >>> n = pt1h.ordinal(datetime(2024, 3, 1, 9, 47))
            >>> pt1h.datetime(n)
            datetime.datetime(2024, 3, 1, 9, 0)
            >>> pt1h.datetime(n + 1)
            datetime.datetime(2024, 3, 1, 10, 0)
        """

    def floor(self, datetime_obj: dt.datetime) -> dt.datetime:
        """Return the first instant of the interval that contains the supplied datetime.

        Shorthand for ``period.datetime(period.ordinal(datetime_obj))`` - snapping a timestamp onto this
        period's grid. Unlike truncating with a :class:`datetime.timedelta`, it works for calendar periods and
        for periods carrying an offset.

        Args:
            datetime_obj: The datetime to floor. Any tzinfo it carries is ignored, as in :meth:`ordinal`.

        Returns:
            A datetime object marking the first instant of the interval containing `datetime_obj`, carrying this
            Period's own tzinfo

        Examples:
            >>> from datetime import datetime
            >>> reading = datetime(2024, 3, 15, 9, 47, 30)
            >>> Period.of_minutes(15).floor(reading)
            datetime.datetime(2024, 3, 15, 9, 45)
            >>> Period.of_months(1).floor(reading)
            datetime.datetime(2024, 3, 1, 0, 0)

            An offset moves every boundary, and with it what a timestamp floors to.

            >>> Period.of_days(1).with_hour_offset(9).floor(datetime(2024, 3, 15, 7, 30))
            datetime.datetime(2024, 3, 14, 9, 0)

            A floored datetime always lands on a boundary.

            >>> pt15m = Period.of_minutes(15)
            >>> pt15m.is_aligned(pt15m.floor(reading))
            True
        """
        return self.datetime(self.ordinal(datetime_obj))

    def interval(self, datetime_obj: dt.datetime) -> tuple[dt.datetime, dt.datetime]:
        """Return the bounds of the interval containing the supplied datetime, as a (start, end) pair.

        The pair is half-open - ``start <= d < end`` for every datetime `d` in the interval - so `end` is the
        first instant of the next interval and belongs to that one. `start` is what :meth:`floor` returns.

        Args:
            datetime_obj: The datetime whose interval is wanted. Any tzinfo it carries is ignored, as in
                :meth:`ordinal`.

        Returns:
            A (start, end) tuple of datetimes, both carrying this Period's own tzinfo

        Examples:
            >>> from datetime import datetime
            >>> Period.of_hours(1).interval(datetime(2024, 3, 15, 9, 47))
            (datetime.datetime(2024, 3, 15, 9, 0), datetime.datetime(2024, 3, 15, 10, 0))

            Calendar intervals work the same way, despite their varying length.

            >>> Period.of_months(1).interval(datetime(2024, 2, 10))
            (datetime.datetime(2024, 2, 1, 0, 0), datetime.datetime(2024, 3, 1, 0, 0))

        See also:
            :meth:`range`, which yields interval starts this can turn into bounded intervals.
        """
        ordinal = self.ordinal(datetime_obj)
        return self.datetime(ordinal), self.datetime(ordinal + 1)

    def range(self, start: dt.datetime, end: dt.datetime) -> Iterator[dt.datetime]:
        """Yield the start of every interval overlapping the half-open window from `start` to `end`.

        The first value is the start of the interval *containing* `start`, which may fall before it; the last is
        the start of the last interval that begins before `end`. An interval is included when any part of it
        falls in the window, so the first and last may both extend beyond it. The window is empty if `end` is
        not after `start`.

        Args:
            start: The start datetime of the range window.
            end: The end datetime of the range window.

        Yields:
            The first instant of each overlapping interval, in order.

        Examples:
            >>> from datetime import datetime
            >>> pt6h = Period.of_hours(6)
            >>> for start in pt6h.range(datetime(2024, 3, 1), datetime(2024, 3, 2)):
            ...     print(start)
            2024-03-01 00:00:00
            2024-03-01 06:00:00
            2024-03-01 12:00:00
            2024-03-01 18:00:00

            A window that starts mid-interval still yields that whole interval ...

            >>> for start in pt6h.range(datetime(2024, 3, 1, 3), datetime(2024, 3, 1, 13)):
            ...     print(start)
            2024-03-01 00:00:00
            2024-03-01 06:00:00
            2024-03-01 12:00:00

            ... and calendar periods need no special handling.

            >>> for start in Period.of_months(1).range(datetime(2024, 1, 15), datetime(2024, 4, 1)):
            ...     print(start)
            2024-01-01 00:00:00
            2024-02-01 00:00:00
            2024-03-01 00:00:00
        """
        if naive(end) <= naive(start):
            return
        end_ordinal = self.ordinal(end)
        if not self.is_aligned(end):
            # `end` falls mid-interval, so that interval overlaps the window and is included.
            end_ordinal += 1
        for ordinal in range(self.ordinal(start), end_ordinal):
            yield self.datetime(ordinal)

    def is_aligned(self, datetime_obj: dt.datetime) -> bool:
        """Return True if the supplied datetime is exactly the start of one of this period's intervals.

        Use it to check that a timestamp really falls on a period boundary before treating it as an interval
        start - e.g. that a value claiming to be hourly is on the hour, or that a reading sits on the 09:00 boundary
        of a hydrological day.

        Args:
            datetime_obj: The datetime to test

        Returns:
            True if the datetime lies at the start of an interval, False otherwise

        Examples:
            >>> from datetime import datetime
            >>> pt1h = Period.of_hours(1)
            >>> pt1h.is_aligned(datetime(2024, 3, 1, 9, 0))
            True
            >>> pt1h.is_aligned(datetime(2024, 3, 1, 9, 47))
            False

            An offset moves every boundary, and with it what counts as aligned.

            >>> water_day = Period.of_days(1).with_hour_offset(9)
            >>> water_day.is_aligned(datetime(2024, 3, 1, 9, 0))
            True
            >>> water_day.is_aligned(datetime(2024, 3, 1, 0, 0))
            False
        """
        ordinal = self.ordinal(datetime_obj)
        datetime_obj2 = self.datetime(ordinal)
        return naive(datetime_obj) == naive(datetime_obj2)

    def base_period(self) -> "Period":
        """Return this period stripped of any offset and origin, keeping only its step and multiplier.

        A "base period" is one whose intervals fall on the natural boundaries of its unit, with un-shifted
        ordinals - exactly what the unit factories such as :meth:`of_days` and :meth:`of_months` produce.

        A period carrying an offset or an origin unwraps the period beneath it, so both are discarded.

        To clear only one of the two, use :meth:`without_offset` or :meth:`without_ordinal_shift`.

        Returns:
            A Period with the same step and multiplier as this one, but no date/time offset and no ordinal shift

        Examples:
            >>> from datetime import datetime

            An offset is discarded ...

            >>> water_day = Period.of_days(1).with_hour_offset(9)
            >>> water_day.base_period()
            P1D

            ... and so is an origin, together with any offset beneath it.

            >>> water_day.with_origin(datetime(1883, 1, 1)).base_period()
            P1D
        """
        return self

    def with_year_offset(self, year_amount: int) -> "Period":
        """Return a copy of this Period with every boundary shifted by `year_amount` years."""
        return self.with_month_offset(year_amount * 12)

    def with_month_offset(self, month_amount: int) -> "Period":
        """Return a copy of this Period with every boundary shifted by `month_amount` months."""
        return build_offset_period(self._properties.with_month_offset(month_amount))

    def with_day_offset(self, day_amount: int) -> "Period":
        """Return a copy of this Period with every boundary shifted by `day_amount` days."""
        return self.with_second_offset(day_amount * 86_400)

    def with_hour_offset(self, hour_amount: int) -> "Period":
        """Return a copy of this Period with every boundary shifted by `hour_amount` hours."""
        return self.with_second_offset(hour_amount * 3_600)

    def with_minute_offset(self, minute_amount: int) -> "Period":
        """Return a copy of this Period with every boundary shifted by `minute_amount` minutes."""
        return self.with_second_offset(minute_amount * 60)

    def with_second_offset(self, second_amount: int) -> "Period":
        """Return a copy of this Period with every boundary shifted by `second_amount` seconds."""
        return self.with_microsecond_offset(second_amount * 1_000_000)

    def with_microsecond_offset(self, microsecond_amount: int) -> "Period":
        """Return a copy of this Period with every boundary shifted by `microsecond_amount` microseconds."""
        return build_offset_period(self._properties.with_microsecond_offset(microsecond_amount))

    def with_tzinfo(self, tzinfo: dt.tzinfo | None) -> "Period":
        """Return a copy of this Period labelled with `tzinfo`. See :doc:`/user_guide/timezones`."""
        properties = self._properties
        if properties.tzinfo == tzinfo:
            return self
        return build_shifted_period(properties.with_tzinfo(tzinfo))

    def without_offset(self) -> "Period":
        """Return a Period derived from this one but with no date/time offset.

        Any ordinal shift is kept: use :meth:`without_ordinal_shift` to clear that instead, or
        :meth:`base_period` to clear both.

        Returns:
            A Period object
        """
        properties = self._properties
        month_offset = properties.month_offset
        microsecond_offset = properties.microsecond_offset
        if (month_offset == 0) and (microsecond_offset == 0):
            return self
        return build_shifted_period(replace(properties, month_offset=0, microsecond_offset=0))

    def without_ordinal_shift(self) -> "Period":
        """Return a Period derived from this one but with no ordinal shift.

        The returned Period splits the timeline in exactly the same way as this one, but the ordinal values
        differ. Any date/time offset is kept: use :meth:`without_offset` to clear that instead, or
        :meth:`base_period` to clear both.

        Returns:
            A Period object
        """
        properties = self._properties
        if properties.ordinal_shift == 0:
            return self
        return build_offset_period(replace(properties, ordinal_shift=0))

    def with_origin(self, origin_date_time: dt.datetime) -> "Period":
        """Return a Period derived from this one but with the origin set to the specified datetime.

        The date/time offset and ordinal shift of this Period are discarded and recalculated such that for the resulting
        Period object the following are True:

        >>> from datetime import datetime
        >>> origin_date_time = datetime(2024, 1, 1)
        >>> period = Period.of_days(7).with_origin(origin_date_time)
        >>> period.ordinal(origin_date_time)
        0
        >>> period.is_aligned(origin_date_time)
        True

        Args:
            origin_date_time: The datetime to become ordinal 0, and the start of an interval

        Returns:
            A Period object
        """
        base_period = self.base_period()
        properties = base_period._properties
        origin_ordinal = base_period.ordinal(origin_date_time)
        floor_date_time = base_period.datetime(origin_ordinal)
        if properties.step in (Step.MICROSECONDS, Step.SECONDS):
            timedelta = naive(origin_date_time) - naive(floor_date_time)
            offset_months = 0
            offset_microseconds = total_microseconds(timedelta)
        else:
            offset_months = month_ordinal(origin_date_time) - month_ordinal(floor_date_time)
            origin2_date_time = month_shift(origin_date_time, 0 - offset_months)
            timedelta = naive(origin2_date_time) - naive(floor_date_time)
            offset_microseconds = total_microseconds(timedelta)
        return build_shifted_period(
            replace(
                properties,
                month_offset=offset_months,
                microsecond_offset=offset_microseconds,
                tzinfo=origin_date_time.tzinfo,
                ordinal_shift=0,
            )
            .normalise_offsets()
            .with_ordinal_shift(0 - origin_ordinal)
        )

    def count(self, other: "Period") -> int | None:
        """Return how many intervals of this period fit into each interval of `other`, or None if there is no
        constant number.

        A count exists when this period's intervals fit inside `other`'s exactly: one of them starts where the
        interval of `other` starts, another ends where it ends, and no part-intervals fall in between. That
        whole number is returned, and it is the same for every interval across the timeline - e.g. twenty-four hours
        in a day, twelve months in a year.

        Two situations have no such number, and both return None:

        * **Aligned, but not constant.** The boundaries line up, but the count differs between intervals. Days
          divide every month cleanly, yet months may have 28 to 31 days, so there is no single answer.
        * **Not aligned.** Intervals of this period straddle the boundaries of `other`, so no interval of
          `other` contains a whole number of them. This also covers this period simply being the larger of the
          two.

        Use :meth:`is_subperiod_of` to tell the two apart: it is True in the first case and False in the second.

        Args:
            other: The period whose intervals this period's intervals are counted within

        Returns:
            The number of intervals of this period per interval of `other`, the same for every interval on the
            timeline; or None if no such number exists

        Examples:
            >>> pt1h, p1d, p1m, p1y = (
            ...     Period.of_hours(1),
            ...     Period.of_days(1),
            ...     Period.of_months(1),
            ...     Period.of_years(1),
            ... )

            The ordinary case: a whole number, the same for every interval on the timeline.

            >>> pt1h.count(p1d)
            24
            >>> p1m.count(p1y)
            12

            Aligned, but a month is 28-31 days, so no constant count exists.

            >>> print(p1d.count(p1m))
            None
            >>> p1d.is_subperiod_of(p1m)
            True

            A larger period never fits inside a smaller one.

            >>> print(p1d.count(pt1h))
            None
            >>> p1d.is_subperiod_of(pt1h)
            False

            An offset on one of them breaks the alignment ...

            >>> pt1h_t1m = Period.of_hours(1).with_minute_offset(1)
            >>> print(pt1h_t1m.count(p1d))
            None

            ... but not if both carry the same offset.

            >>> pt1h_t1m.count(Period.of_days(1).with_minute_offset(1))
            24

        See also:
            :meth:`is_subperiod_of`, for whether the intervals nest at all.
        """
        return self._properties.count(other._properties)

    def is_subperiod_of(self, other: "Period") -> bool:
        """Return True if every interval of this period falls entirely inside a single interval of `other`.

        Each of this period's intervals must lie wholly within one of `other`'s, never straddling a boundary -
        but different intervals of `other` may hold different numbers of them. A day is a subperiod of a month for
        exactly that reason: no day ever spans a month boundary, even though months hold 28 to 31 of them.

        It follows that a larger period is never a subperiod of a smaller one, and that a period is always a
        subperiod of itself. The two must also agree on timezone: a period at UTC is not a subperiod of one at
        +05:00, nor of a naive one.

        Args:
            other: The period whose intervals must contain this period's

        Returns:
            True if every interval of this period lies within one interval of `other`, False otherwise

        Examples:
            >>> pt1h, p1d, p1m = Period.of_hours(1), Period.of_days(1), Period.of_months(1)

            An hour never straddles a midnight boundary, nor a day a month boundary - even though months
            vary in length.

            >>> pt1h.is_subperiod_of(p1d)
            True
            >>> p1d.is_subperiod_of(p1m)
            True

            The larger period is never contained by the smaller.

            >>> p1d.is_subperiod_of(pt1h)
            False

            Offsetting one of them makes its intervals straddle the other's boundaries ...

            >>> pt1h_t1m = Period.of_hours(1).with_minute_offset(1)
            >>> pt1h_t1m.is_subperiod_of(p1d)
            False

            ... unless both are offset alike.

            >>> pt1h_t1m.is_subperiod_of(Period.of_days(1).with_minute_offset(1))
            True
        """
        return self._properties.is_subperiod_of(other._properties)

    def _origin_datetime(self) -> dt.datetime | None:
        """Return this period's origin, or None if it has no usable one.

        A period with an ordinal shift numbers the interval starting at its origin zero, so the origin is
        ``datetime(0)``. The period's tzinfo is left off, since :meth:`of` reads a timezone from an origin that
        carries one.

        Returns:
            The origin, or None if this period has no ordinal shift or its ordinal zero falls outside the
            datetime range
        """
        if self._properties.ordinal_shift == 0:
            return None
        try:
            return naive(self.datetime(0))
        except (ValueError, OverflowError):
            return None

    def _origin_string(self) -> str | None:
        """Return this period's origin as an ISO 8601 date or datetime, or None if it has no usable one.

        The time is dropped when the origin falls at midnight.

        Returns:
            The origin as an ISO 8601 string, or None if this period has no ordinal shift or its ordinal zero
            falls outside the datetime range
        """
        origin = self._origin_datetime()
        if origin is None:
            return None
        if origin.time() == dt.time.min:
            return origin.date().isoformat()
        return origin.isoformat()

    def __str__(self) -> str:
        origin = self._origin_string()
        if origin is None:
            return self._properties.__str__()
        return f"{origin}/{self.iso_duration}"

    def __repr__(self) -> str:
        origin = self._origin_string()
        if origin is None:
            return self._properties.__repr__()
        tzinfo = self.tzinfo
        suffix = f"[{tz_label(tzinfo)}]" if tzinfo is not None else ""
        return f"{origin}/{self.iso_duration}{suffix}"

    def __hash__(self) -> int:
        return self._properties.__hash__()

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Period):
            return NotImplemented
        return self._properties.__eq__(other._properties)

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Period):
            return NotImplemented
        return self._properties.__lt__(other._properties)

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, Period):
            return NotImplemented
        return self._properties.__le__(other._properties)

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, Period):
            return NotImplemented
        return self._properties.__gt__(other._properties)

    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, Period):
            return NotImplemented
        return self._properties.__ge__(other._properties)


class BasePeriod(Period, ABC):
    """A Period whose intervals fall on the natural boundaries of its unit.

    Subclasses set `_step` to the step they implement and read `_n`, the multiplier. An offset or an ordinal
    shift belongs to OffsetPeriod or ShiftedPeriod, which wrap one of these, so neither is legal here.
    """

    _step: ClassVar[Step]

    def __init__(self, properties: Properties) -> None:
        """Store the properties and check the invariants every base period holds.

        Args:
            properties: The specification of the Period to build

        Raises:
            PeriodValidationError: If the step is not this subclass's, or there is an offset or ordinal shift
        """
        super().__init__(properties)
        name = type(self).__name__

        if properties.step != self._step:
            raise PeriodValidationError(f"Illegal step: '{properties.step}'. Must be: {self._step}.")

        if properties.month_offset != 0:
            raise PeriodValidationError(f"Illegal month offset: {properties.month_offset}. Must be '0' for a '{name}'.")

        if properties.microsecond_offset != 0:
            raise PeriodValidationError(
                f"Illegal microsecond offset: {properties.microsecond_offset}. Must be '0' for a '{name}'."
            )

        if properties.ordinal_shift != 0:
            raise PeriodValidationError(
                f"Illegal ordinal shift: {properties.ordinal_shift}. Must be '0' for a '{name}'."
            )

        self._n = properties.multiplier


class MonthsPeriod(BasePeriod):
    """A period of "n" months, starting at midnight on the first day of the first month of the period."""

    _step = Step.MONTHS

    @override
    def ordinal(self, datetime_obj: dt.datetime) -> int:
        return month_ordinal(datetime_obj) // self._n

    @override
    def datetime(self, ordinal: int) -> dt.datetime:
        year, month = year_month(ordinal * self._n)
        return dt.datetime(year, month, 1, hour=0, minute=0, second=0, tzinfo=self.tzinfo)


class SecondsPeriod(BasePeriod):
    """A period of "n" seconds, starting at the point in the day that is evenly divisible by n seconds."""

    _step = Step.SECONDS

    @override
    def ordinal(self, datetime_obj: dt.datetime) -> int:
        return gregorian_seconds(datetime_obj) // self._n

    @override
    def datetime(self, ordinal: int) -> dt.datetime:
        gregorian_ordinal, second_of_day = divmod(ordinal * self._n, 86_400)
        return (dt.datetime.fromordinal(gregorian_ordinal) + dt.timedelta(seconds=second_of_day)).replace(
            tzinfo=self.tzinfo
        )


class MicrosecondsPeriod(BasePeriod):
    """A period of "n" microseconds, starting at the point in the day that is evenly divisible by n microseconds."""

    _step = Step.MICROSECONDS

    @override
    def ordinal(self, datetime_obj: dt.datetime) -> int:
        seconds = gregorian_seconds(datetime_obj)
        microseconds = seconds * 1_000_000 + datetime_obj.microsecond
        return microseconds // self._n

    @override
    def datetime(self, ordinal: int) -> dt.datetime:
        total_seconds, microseconds = divmod(ordinal * self._n, 1_000_000)
        gregorian_ordinal, second_of_day = divmod(total_seconds, 86_400)
        return (
            dt.datetime.fromordinal(gregorian_ordinal) + dt.timedelta(seconds=second_of_day, microseconds=microseconds)
        ).replace(tzinfo=self.tzinfo)


def build_shifted_period(properties: Properties) -> Period:
    """Return a Period with a possible month/second offset and also a possible ordinal_shift.

    Args:
        properties: The specification of the Period to build

    Returns:
        A Period object
    """
    if properties.ordinal_shift != 0:
        return ShiftedPeriod(properties)
    return build_offset_period(properties)


def build_offset_period(properties: Properties) -> Period:
    """Return a Period with a possible month or second offset but no ordinal_shift.

    Args:
        properties: The specification of the Period to build

    Returns:
        A Period object
    """
    if properties.ordinal_shift != 0:
        raise PeriodValidationError(f"Illegal ordinal shift: {properties.ordinal_shift}. Must be '0'.")

    if (properties.month_offset != 0) or (properties.microsecond_offset != 0):
        return OffsetPeriod(properties)
    return build_base_period(properties)


def build_base_period(properties: Properties) -> Period:
    """Return a Period with no month or second offset and no ordinal_shift.

    Examines the supplied Properties and chooses the concrete Period subclass that can perform the required
    interval calculations.

    Args:
        properties: The specification of the Period to build

    Returns:
        A Period object
    """
    step = properties.step

    if step == Step.MONTHS:
        return MonthsPeriod(properties)

    if step == Step.SECONDS:
        return SecondsPeriod(properties)

    if step == Step.MICROSECONDS:
        return MicrosecondsPeriod(properties)

    raise illegal_step(step)


class OffsetPeriod(Period):
    """A period that wraps another period but allows the period to start at a different point in time."""

    def __init__(self, properties: Properties) -> None:
        super().__init__(properties)

        if not ((properties.month_offset > 0) or (properties.microsecond_offset > 0)):
            raise PeriodValidationError(
                f"No offset detected in month_offset or microsecond_offset: "
                f"{properties.month_offset}/{properties.microsecond_offset}"
            )

        if properties.ordinal_shift != 0:
            raise PeriodValidationError(f"Illegal ordinal shift: {properties.ordinal_shift}. Must be '0'.")

        self._base_period = build_base_period(
            replace(properties, month_offset=0, microsecond_offset=0, ordinal_shift=0)
        )

    @override
    def ordinal(self, datetime_obj: dt.datetime) -> int:
        return self._base_period.ordinal(timeline.retreat(datetime_obj, self.month_offset, self.microsecond_offset))

    @override
    def datetime(self, ordinal: int) -> dt.datetime:
        return timeline.advance(self._base_period.datetime(ordinal), self.month_offset, self.microsecond_offset)

    @override
    def base_period(self) -> "Period":
        """Discard this period's offset by returning the un-offset period it wraps."""
        return self._base_period


class ShiftedPeriod(Period):
    """A period that wraps another period but adjusts the ordinal by a specified amount.

    This allows the 'origin' of a Period to be defined, where the origin is the datetime that has an ordinal of 0.
    """

    def __init__(self, properties: Properties) -> None:
        super().__init__(properties)

        if properties.ordinal_shift == 0:
            raise PeriodValidationError(f"Illegal ordinal shift: {properties.ordinal_shift}. Must not be '0'.")

        offset_period = build_offset_period(replace(properties, ordinal_shift=0))
        self._offset_period = offset_period
        self._ordinal_shift = properties.ordinal_shift

    @override
    def ordinal(self, datetime_obj: dt.datetime) -> int:
        return self._offset_period.ordinal(datetime_obj) + self._ordinal_shift

    @override
    def datetime(self, ordinal: int) -> dt.datetime:
        return self._offset_period.datetime(ordinal - self._ordinal_shift)

    @override
    def base_period(self) -> "Period":
        """Discard this period's origin, and any offset beneath it, by unwrapping both layers."""
        return self._offset_period.base_period()
