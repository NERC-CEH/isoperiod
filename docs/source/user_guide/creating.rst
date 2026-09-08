.. _creating_periods:

================
Creating periods
================

.. rst-class:: lead

    Every way to build a :class:`~isoperiod.Period`, and what each one means.

:class:`~isoperiod.Period` is abstract - you never instantiate it directly. Instead, a set of static factory
methods are available to build a period in various ways. All of them return a fully-formed period.

.. code-block:: python

    from datetime import datetime, timedelta
    from isoperiod import Period

From a named unit
=================

The most direct route. Each factory takes a count of that unit:

.. list-table::
   :header-rows: 1
   :widths: 40 25 35

   * - Factory
     - Example
     - Intervals start at
   * - :meth:`~isoperiod.Period.of_years`
     - ``Period.of_years(1)``
     - 00:00 on 1 January
   * - :meth:`~isoperiod.Period.of_months`
     - ``Period.of_months(3)``
     - 00:00 on the 1st
   * - :meth:`~isoperiod.Period.of_days`
     - ``Period.of_days(1)``
     - midnight
   * - :meth:`~isoperiod.Period.of_hours`
     - ``Period.of_hours(6)``
     - the top of the hour
   * - :meth:`~isoperiod.Period.of_minutes`
     - ``Period.of_minutes(15)``
     - the top of the minute
   * - :meth:`~isoperiod.Period.of_seconds`
     - ``Period.of_seconds(30)``
     - a whole second
   * - :meth:`~isoperiod.Period.of_microseconds`
     - ``Period.of_microseconds(40_000)``
     - a whole microsecond

The count must be greater than zero; anything else raises
:class:`~isoperiod.PeriodValidationError`.

From a string
=============

:meth:`~isoperiod.Period.of` accepts three supported string formats and tries each in turn:

1. Plain ISO 8601 duration
--------------------------

The `ISO 8601 duration <https://en.wikipedia.org/wiki/ISO_8601#Durations>`_ form: ``P``, then a date part, then
``T`` and a time part. Parsing is case-insensitive.

.. code-block:: python

    p1y = Period.of("P1Y")          # 1 year
    p3m = Period.of("P3M")          # 3 months (a quarter)
    p1d = Period.of("P1D")          # 1 day
    pt15m = Period.of("PT15M")      # 15 minutes
    pt25hz = Period.of("PT0.04S")   # 40 ms - 25 Hz sampling

Components combine:

.. code-block:: python

    assert Period.of("P1Y6M") == Period.of_months(18)
    assert Period.of("P1DT12H") == Period.of_hours(36)
    assert Period.of("PT1H30M") == Period.of_minutes(90)

.. warning::

   A period cannot mix calendar units (years, months) with clock units (days and below), because months have no
   fixed length in seconds. ``"P1M1D"`` raises :class:`~isoperiod.PeriodValidationError`.

:meth:`~isoperiod.Period.of_iso_duration` parses this form and only this form - useful when you want to reject the
extended syntaxes explicitly.

2. Duration with an offset
--------------------------

An extension of the ISO 8601 format, written ``<duration>+<offset>``. The offset is itself a duration, and shifts
every interval boundary forwards by that amount:

.. code-block:: python

    assert Period.of("P1D+T9H") == Period.of_days(1).with_hour_offset(9)
    assert Period.of("PT15M+T5M") == Period.of_minutes(15).with_minute_offset(5)
    assert Period.of("P1Y+9M") == Period.of_years(1).with_month_offset(9)
    assert Period.of("P1Y+9MT9H") == Period.of_years(1).with_month_offset(9).with_hour_offset(9)

:meth:`~isoperiod.Period.of_duration` accepts both this form and a plain duration.

3. Duration with an origin
--------------------------

Written ``<start>/<duration>``. The ``start`` datetime becomes ordinal ``0`` **and** a boundary of the period, which
fixes the grid for periods that have no meaningful natural boundary:

.. code-block:: python

    p = Period.of("2024-01-01/P7D")

    assert p.ordinal(datetime(2024, 1, 1)) == 0
    assert p.is_aligned(datetime(2024, 1, 1)) == True
    assert p.datetime(1) == datetime(2024, 1, 8)

The start may be a full datetime, or a reduced-precision date - a bare year or year-month is padded to its first
instant, following ISO 8601:

.. code-block:: python

    assert Period.of("2024/P1Y") == Period.of("2024-01-01/P1Y")
    assert Period.of("1883-01-01T09:00/P1D") == Period.of("P1D+T9H").with_origin(datetime(1883, 1, 1, 9, 0))

:meth:`~isoperiod.Period.of_date_and_duration` parses this form only.

See :doc:`offsets` for the difference between an offset and an origin.

From a timedelta
================

:meth:`~isoperiod.Period.of_timedelta` builds a period matching any fixed-length duration:

.. code-block:: python

    assert Period.of_timedelta(timedelta(minutes=30)) == Period.of_minutes(30)
    assert Period.of_timedelta(timedelta(milliseconds=20)) == Period.of("PT0.02S")

There is no equivalent for months and years - a ``timedelta`` cannot represent them.

Handling bad input
==================

Two exceptions are raised when a period cannot be built, both subclasses of :class:`~isoperiod.PeriodError`:

:class:`~isoperiod.PeriodParsingError`
    The string does not match any supported format at all.

:class:`~isoperiod.PeriodValidationError`
    The string parsed, but does not describe a usable period - a zero-length duration, or one mixing calendar and
    clock units.

Catch :class:`~isoperiod.PeriodError` to handle both:

.. code-block:: python

    from isoperiod import Period, PeriodError

    def parse_resolution(text: str) -> Period | None:
        try:
            return Period.of(text)
        except PeriodError:
            return None

    assert parse_resolution("every 15 mins") is None  # PeriodParsingError
    assert parse_resolution("P1M1D") is None          # PeriodValidationError
