"""The Period class: the abstract Period base class, its concrete implementations, and the factory
functions that choose the right implementation for a given Properties object.
"""

import datetime as dt
from abc import ABC, abstractmethod
from dataclasses import replace
from typing import Any, override

from isoperiod import parsing, timeline
from isoperiod.enums import Step
from isoperiod.exceptions import PeriodParsingError, PeriodValidationError, illegal_step
from isoperiod.properties import Properties
from isoperiod.timeline import (
    gregorian_seconds,
    month_ordinal,
    month_shift,
    naive,
    total_microseconds,
    year_month,
)


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

    Examples:
        .. code-block:: python

            from datetime import datetime, timedelta

            p1h = Period.of_hours(1)
            d = datetime(2024, 3, 1, 9, 47)

            # Which hour is 09:47 in, and when did that hour start and end?
            n = p1h.ordinal(d)
            assert p1h.datetime(n) == datetime(2024, 3, 1, 9, 0)
            assert p1h.datetime(n + 1) == datetime(2024, 3, 1, 10, 0)

            # Ordinals are consecutive integers, so interval arithmetic is integer arithmetic.
            assert p1h.ordinal(d) + 24 == p1h.ordinal(d + timedelta(days=1))

            # Months work the same way, despite their varying length.
            p1m = Period.of_months(1)
            assert p1m.datetime(p1m.ordinal(datetime(2024, 3, 15))) == datetime(2024, 3, 1)

    Offsets:
        By default a Period's intervals fall on the natural boundaries of their unit: a one-day period runs
        midnight to midnight, a one-hour period from the top of one hour to the top of the next, a one-year
        period from January 1st. An **offset** moves every one of those boundaries by a fixed amount, so the
        intervals keep their size but start somewhere else.

        This is what lets a Period describe a "day" that isn't a calendar day, e.g. a hydrological day measured
        from 09:00, or a business year starting in October:

        .. code-block:: python

            from datetime import datetime

            water_day = Period.of_days(1).with_hour_offset(9)     # days running 09:00 -> 09:00
            d = datetime(2024, 3, 15, 7, 30)

            # 07:30 belongs to the water day that began at 09:00 the *previous* day.
            assert water_day.datetime(water_day.ordinal(d)) == datetime(2024, 3, 14, 9, 0)

        The offset applies to every interval on the timeline, not just the first - it sets the *phase* of the
        repeating pattern. It is built with the ``with_*_offset`` methods, and written as ``<duration>+<offset>``
        in string form (``"P1D+T9H"``, ``"P1Y+9M"``). That syntax is this package's own extension of the ISO 8601
        duration format.

    Period is abstract; build one with a factory method:

    * :meth:`of_years` - "n" calendar years, from January 1st.
    * :meth:`of_months` - "n" calendar months, from the 1st of the month.
    * :meth:`of_days` - "n" days, from midnight.
    * :meth:`of_hours` - "n" hours, from the top of the hour.
    * :meth:`of_minutes` - "n" minutes, from the top of the minute.
    * :meth:`of_seconds` - "n" whole seconds.
    * :meth:`of_microseconds` - "n" microseconds; the finest resolution a Period can have.

    From a string or a timedelta:

    * :meth:`of` - all three string formats (plain duration, ``+offset``, ``<start>/<duration>``), tried in
      turn. Use this when you do not know which form you have.
    * :meth:`of_iso_duration` - a plain ISO 8601 duration only, e.g. ``"P1Y"``, ``"PT15M"``.
    * :meth:`of_duration` - a plain ISO 8601 duration, or the extended ``<duration>+<offset>`` form described
      above, e.g. ``"P1D+T9H"``.
    * :meth:`of_date_and_duration` - the ``<start>/<duration>`` form, e.g. ``"1883-01-01/P1D"``. The start
      date sets the period's origin, not its offset - it is the datetime given ordinal 0.
    * :meth:`of_timedelta` - a period matching a :class:`datetime.timedelta`.

    Each factory returns a fully-formed Period, which the ``with_*`` methods then refine; every one of those
    returns a new Period rather than mutating the original:

    .. code-block:: python

        from datetime import timezone

        Period.of("PT15M")                             # every 15 minutes
        Period.of_days(1).with_hour_offset(9)          # every day, starting at 09:00
        Period.of_years(1).with_tzinfo(timezone.utc)

    Period instances are immutable and hashable, so they work in sets and as dict keys. They also sort, with the
    same caveat that applies to datetime objects: comparing Periods whose tzinfo values are mismatched raises
    ``TypeError`` rather than producing an order.
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
        """Return an "n"-year Period

        Args:
            no_of_years: The number of years in the period

        Returns:
            A Period object
        """
        return build_base_period(Properties.of_months(no_of_years * 12))

    @staticmethod
    def of_months(no_of_months: int) -> "Period":
        """Return an "n"-month Period

        Args:
            no_of_months: The number of months in the period

        Returns:
            A Period object
        """
        return build_base_period(Properties.of_months(no_of_months))

    @staticmethod
    def of_days(no_of_days: int) -> "Period":
        """Return an "n"-day Period

        Args:
            no_of_days: The number of days in the period

        Returns:
            A Period object
        """
        return build_base_period(Properties.of_seconds(no_of_days * 86_400))

    @staticmethod
    def of_hours(no_of_hours: int) -> "Period":
        """Return an "n"-hour Period

        Args:
            no_of_hours: The number of hours in the period

        Returns:
            A Period object
        """
        return build_base_period(Properties.of_seconds(no_of_hours * 3_600))

    @staticmethod
    def of_minutes(no_of_minutes: int) -> "Period":
        """Return an "n"-minute Period

        Args:
            no_of_minutes: The number of minutes in the period

        Returns:
            A Period object
        """
        return build_base_period(Properties.of_seconds(no_of_minutes * 60))

    @staticmethod
    def of_seconds(no_of_seconds: int) -> "Period":
        """Return an "n"-second Period

        Args:
            no_of_seconds: The number of seconds in the period

        Returns:
            A Period object
        """
        return build_base_period(Properties.of_seconds(no_of_seconds))

    @staticmethod
    def of_microseconds(no_of_microseconds: int) -> "Period":
        """Return an "n"-microsecond Period

        Args:
            no_of_microseconds: The number of microseconds in the period

        Returns:
            A Period object
        """
        return build_base_period(Properties.of_microseconds(no_of_microseconds))

    @staticmethod
    def of_timedelta(timedelta: dt.timedelta) -> "Period":
        """Return a Period that matches a timedelta

        Args:
            timedelta: The timedelta of the period

        Returns:
            A Period object
        """
        return build_base_period(Properties.of_microseconds(total_microseconds(timedelta)))

    def __init__(self, properties: Properties) -> None:
        self._properties = properties

    @property
    def iso_duration(self) -> str:
        """The standard ISO 8601 duration string of this period"""
        return self._properties.get_iso8601()

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
        return self._properties.get_timedelta()

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
        return self._properties.pl_interval()

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
        return self._properties.pl_offset()

    @property
    def offset(self) -> str:
        """Return a string that captures the month and microsecond offsets of this period which conforms to the offset
        bit of the string required in a Period.of_duration string.

        Returns:
            A string suitable for use with Period of_duration string
        """
        return self._properties.offset()

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
            .. code-block:: python

                from datetime import datetime

                p1m = Period.of_months(1)
                d = datetime(2024, 3, 15, 9, 47)

                # Every datetime in March 2024 shares one ordinal ...
                n = p1m.ordinal(d)
                assert n == p1m.ordinal(datetime(2024, 3, 1))
                assert n == p1m.ordinal(datetime(2024, 3, 31, 23, 59))

                # ... which Period.datetime() turns back into the start of that month.
                assert p1m.datetime(n) == datetime(2024, 3, 1)
                assert p1m.datetime(n) <= d < p1m.datetime(n + 1)

        Note:
            An ordinal only means anything to the Period that produced it. Each period numbers the timeline in
            its own units, and feeding one period's ordinal to another's :meth:`datetime` gives a wrong answer
            rather than an error:

            .. code-block:: python

                from datetime import datetime

                n = Period.of_months(1).ordinal(datetime(2024, 3, 15))
                assert n == 24_290  # months, not days

                assert Period.of_days(1).datetime(n) == datetime(67, 7, 3)  # nonsense, silently
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
            .. code-block:: python

                from datetime import datetime

                p1h = Period.of_hours(1)
                n = p1h.ordinal(datetime(2024, 3, 1, 9, 47))

                assert p1h.datetime(n) == datetime(2024, 3, 1, 9, 0)       # start of the interval
                assert p1h.datetime(n + 1) == datetime(2024, 3, 1, 10, 0)  # start of the next one
        """

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
            .. code-block:: python

                from datetime import datetime

                p1h = Period.of_hours(1)
                assert p1h.is_aligned(datetime(2024, 3, 1, 9, 0)) == True
                assert p1h.is_aligned(datetime(2024, 3, 1, 9, 47)) == False

                # An offset moves every boundary, and with it what counts as aligned.
                water_day = Period.of_days(1).with_hour_offset(9)
                assert water_day.is_aligned(datetime(2024, 3, 1, 9, 0)) == True
                assert water_day.is_aligned(datetime(2024, 3, 1, 0, 0)) == False
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
            .. code-block:: python

                from datetime import datetime

                assert Period.of_days(1).base_period() == Period.of_days(1)

                # An offset is discarded ...
                water_day = Period.of_days(1).with_hour_offset(9)
                assert water_day.base_period() == Period.of_days(1)

                # ... and so is an origin, together with any offset beneath it.
                shifted = water_day.with_origin(datetime(1883, 1, 1))
                assert shifted.base_period() == Period.of_days(1)
        """
        return self

    def with_year_offset(self, year_amount: int) -> "Period":
        """Return a Period derived from this one but with the specified year offset

        Args:
            year_amount: The year offset of the new Period

        Returns:
            A Period object
        """
        return self.with_month_offset(year_amount * 12)

    def with_month_offset(self, month_amount: int) -> "Period":
        """Return a Period derived from this one but with the specified month offset

        Args:
            month_amount: The month offset of the new Period

        Returns:
            A Period object
        """
        return build_offset_period(self._properties.with_month_offset(month_amount))

    def with_day_offset(self, day_amount: int) -> "Period":
        """Return a Period derived from this one but with the specified day offset

        Args:
            day_amount: The day offset of the new Period

        Returns:
            A Period object
        """
        return self.with_second_offset(day_amount * 86_400)

    def with_hour_offset(self, hour_amount: int) -> "Period":
        """Return a Period derived from this one but with the specified hour offset

        Args:
            hour_amount: The hour offset of the new Period

        Returns:
            A Period object
        """
        return self.with_second_offset(hour_amount * 3_600)

    def with_minute_offset(self, minute_amount: int) -> "Period":
        """Return a Period derived from this one but with the specified minute offset

        Args:
            minute_amount: The minute offset of the new Period

        Returns:
            A Period object
        """
        return self.with_second_offset(minute_amount * 60)

    def with_second_offset(self, second_amount: int) -> "Period":
        """Return a Period derived from this one but with the specified second offset

        Args:
            second_amount: The second offset of the new Period

        Returns:
            A Period object
        """
        return self.with_microsecond_offset(second_amount * 1_000_000)

    def with_microsecond_offset(self, microsecond_amount: int) -> "Period":
        """Return a Period derived from this one but with the specified microsecond offset

        Args:
            microsecond_amount: The microsecond offset of the new Period

        Returns:
            A Period object
        """
        return build_offset_period(self._properties.with_microsecond_offset(microsecond_amount))

    def with_tzinfo(self, tzinfo: dt.tzinfo | None) -> "Period":
        """Return a Period derived from this one but with the specified tzinfo

        Args:
            tzinfo: The tzinfo to apply to the new Period

        Returns:
            A Period object
        """
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

        .. code-block:: python

            from datetime import datetime

            origin_date_time = datetime(2024, 1, 1)
            period = Period.of_days(7).with_origin(origin_date_time)

            assert period.ordinal(origin_date_time) == 0
            assert period.is_aligned(origin_date_time) == True

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
            .. code-block:: python

                p1h = Period.of_hours(1)
                p1d = Period.of_days(1)
                p1m = Period.of_months(1)
                p1y = Period.of_years(1)

                # The ordinary case: a whole number, the same for every interval on the timeline.
                assert p1h.count(p1d) == 24
                assert p1m.count(p1y) == 12

                # Aligned, but a month is 28-31 days, so no constant count exists.
                assert p1d.count(p1m) is None
                assert p1d.is_subperiod_of(p1m) == True

                # A larger period never fits inside a smaller one.
                assert p1d.count(p1h) is None
                assert p1d.is_subperiod_of(p1h) == False

                # An offset on one of them breaks the alignment ...
                p1h_1m = Period.of_hours(1).with_minute_offset(1)
                assert p1h_1m.count(p1d) is None

                # ... but not if both carry the same offset.
                p1d_1m = Period.of_days(1).with_minute_offset(1)
                assert p1h_1m.count(p1d_1m) == 24

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
            .. code-block:: python

                p1h = Period.of_hours(1)
                p1d = Period.of_days(1)
                p1m = Period.of_months(1)

                # An hour never straddles a midnight boundary.
                assert p1h.is_subperiod_of(p1d) == True

                # Nor does a day straddle a month boundary, even though months vary in length.
                assert p1d.is_subperiod_of(p1m) == True

                # The larger period is never contained by the smaller.
                assert p1d.is_subperiod_of(p1h) == False

                # Offsetting one of them makes its intervals straddle the other's boundaries ...
                p1h_1m = Period.of_hours(1).with_minute_offset(1)
                assert p1h_1m.is_subperiod_of(p1d) == False

                # ... unless both are offset alike.
                p1d_1m = Period.of_days(1).with_minute_offset(1)
                assert p1h_1m.is_subperiod_of(p1d_1m) == True
        """
        return self._properties.is_subperiod_of(other._properties)

    def _validate_base_period(self, properties: Properties, expected_step: int) -> None:
        """Validate the properties shared by every concrete "base period" subclass (i.e. every Period with no date/time
        offset and no ordinal shift): the step must match what this subclass implements, and there must be no offset or
        ordinal shift, since those are the responsibility of OffsetPeriod/ShiftedPeriod.

        Args:
            properties: The Properties object passed to this subclass's constructor
            expected_step: The step this subclass implements

        Raises:
            PeriodValidationError: If any of the invariants are violated
        """
        if properties.step != expected_step:
            raise PeriodValidationError(f"Illegal step: '{properties.step}'. Must be: {expected_step}.")

        if properties.month_offset != 0:
            raise PeriodValidationError(
                f"Illegal month offset: {properties.month_offset}. Must be '0' for a '{self.__class__.__name__}'."
            )

        if properties.microsecond_offset != 0:
            raise PeriodValidationError(
                f"Illegal microsecond offset: {properties.microsecond_offset}. "
                f"Must be '0' for a '{self.__class__.__name__}'."
            )

        if properties.ordinal_shift != 0:
            raise PeriodValidationError(
                f"Illegal ordinal shift: {properties.ordinal_shift}. Must be '0' for a '{self.__class__.__name__}'."
            )

    def __str__(self) -> str:
        return self._properties.__str__()

    def __repr__(self) -> str:
        return self._properties.__repr__()

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


class MonthsPeriod(Period):
    """A period of "n" months, starting at midnight on the first day of the first month of the period."""

    def __init__(self, properties: Properties) -> None:
        super().__init__(properties)
        self._validate_base_period(properties, Step.MONTHS)
        self._n = properties.multiplier

    @override
    def ordinal(self, datetime_obj: dt.datetime) -> int:
        return month_ordinal(datetime_obj) // self._n

    @override
    def datetime(self, ordinal: int) -> dt.datetime:
        year, month = year_month(ordinal * self._n)
        return dt.datetime(year, month, 1, hour=0, minute=0, second=0, tzinfo=self.tzinfo)


class SecondsPeriod(Period):
    """A period of "n" seconds, starting at the point in the day that is evenly divisible by n seconds."""

    def __init__(self, properties: Properties) -> None:
        super().__init__(properties)
        self._validate_base_period(properties, Step.SECONDS)
        self._n = properties.multiplier

    @override
    def ordinal(self, datetime_obj: dt.datetime) -> int:
        return gregorian_seconds(datetime_obj) // self._n

    @override
    def datetime(self, ordinal: int) -> dt.datetime:
        gregorian_ordinal, second_of_day = divmod(ordinal * self._n, 86_400)
        return (dt.datetime.fromordinal(gregorian_ordinal) + dt.timedelta(seconds=second_of_day)).replace(
            tzinfo=self.tzinfo
        )


class MicrosecondsPeriod(Period):
    """A period of "n" microseconds, starting at the point in the day that is evenly divisible by n microseconds."""

    def __init__(self, properties: Properties) -> None:
        super().__init__(properties)
        self._validate_base_period(properties, Step.MICROSECONDS)
        self._n = properties.multiplier

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
    month_offset = properties.month_offset
    microsecond_offset = properties.microsecond_offset

    if month_offset != 0:
        raise PeriodValidationError(f"Illegal month_offset: {month_offset}. Must be '0'.")

    if microsecond_offset != 0:
        raise PeriodValidationError(f"Illegal microsecond_offset: {microsecond_offset}. Must be '0'.")

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
