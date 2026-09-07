.. _offsets_and_origins:

===================
Offsets and origins
===================

.. rst-class:: lead

    Moving a period's interval boundaries off their natural position.

By default a period's intervals sit on the natural boundaries of their unit: a day runs midnight to midnight, a
year from 1 January. Real measurement regimes often do not. Two mechanisms move the grid, and they answer
different questions:

**Offset**
    *Where are the boundaries?* Shifts every boundary by a fixed amount, keeping the interval size. Written
    ``P1D+T9H``.

**Origin**
    *Which interval is number zero?* Pins the numbering to a chosen datetime, and aligns the boundaries so that
    datetime is one of them. Written ``2024-01-01/P7D``.

.. code-block:: python

    from datetime import datetime, timezone
    from isoperiod import Period

Setting an offset
=================

Each ``with_*_offset`` method returns a **new** period - periods are immutable, so the original is untouched:

.. list-table::
   :header-rows: 1
   :widths: 30 55

   * - Method
     - Example
   * - :meth:`~isoperiod.Period.with_year_offset`
     - ``Period.of_years(10).with_year_offset(1)``
   * - :meth:`~isoperiod.Period.with_month_offset`
     - ``Period.of_years(1).with_month_offset(9)``
   * - :meth:`~isoperiod.Period.with_day_offset`
     - ``Period.of("P7D").with_day_offset(3)``
   * - :meth:`~isoperiod.Period.with_hour_offset`
     - ``Period.of_days(1).with_hour_offset(9)``
   * - :meth:`~isoperiod.Period.with_minute_offset`
     - ``Period.of_minutes(15).with_minute_offset(5)``
   * - :meth:`~isoperiod.Period.with_second_offset`
     - ``Period.of_minutes(1).with_second_offset(30)``
   * - :meth:`~isoperiod.Period.with_microsecond_offset`
     - ``Period.of_seconds(1).with_microsecond_offset(500_000)``

.. warning::

   A month offset only makes sense for a period whose step is months, because a month has no fixed length in
   seconds. ``Period.of_days(1).with_month_offset(1)`` raises :class:`~isoperiod.PeriodValidationError`.

Worked example: the hydrological day
====================================

UK hydrological convention measures a "day" from 09:00 to 09:00. As a period that is a one-day interval offset by
nine hours:

.. code-block:: python

    water_day = Period.of_days(1).with_hour_offset(9)

    # A reading at 07:30 belongs to the water day that began at 09:00 the previous day.
    reading = datetime(2024, 3, 15, 7, 30)
    assert water_day.datetime(water_day.ordinal(reading)) == datetime(2024, 3, 14, 9, 0)

    # A reading at 10:00 belongs to the one that began this morning.
    assert water_day.datetime(water_day.ordinal(datetime(2024, 3, 15, 10, 0))) == datetime(2024, 3, 15, 9, 0)

    # Alignment follows the shifted boundaries.
    assert water_day.is_aligned(datetime(2024, 3, 15, 9, 0)) == True
    assert water_day.is_aligned(datetime(2024, 3, 15, 0, 0)) == False

Worked example: the water year
==============================

The UK water year runs from 09:00 on 1 October. That is a one-year period offset by nine months and nine hours:

.. code-block:: python

    water_year = Period.of("P1Y+9MT9H")

    assert water_year.datetime(water_year.ordinal(datetime(2024, 3, 15))) == datetime(2023, 10, 1, 9, 0)
    assert water_year.datetime(water_year.ordinal(datetime(2024, 11, 15))) == datetime(2024, 10, 1, 9, 0)

Offsets are accounted for when periods are compared, so a hydrological day nests cleanly inside a water year -
while a calendar day, which straddles the 09:00 boundary every 1 October, does not:

.. code-block:: python

    assert Period.of("P1D+T9H").is_subperiod_of(water_year) == True
    assert Period.of_days(1).is_subperiod_of(water_year) == False

    assert Period.of_hours(1).count(Period.of("P1D+T9H")) == 24  # hours still fit a 09:00 day
    assert Period.of_hours(1).is_subperiod_of(Period.of("P1D+T9H30M")) == False

See :doc:`comparing` for the full rules.

Inspecting an offset
====================

.. code-block:: python

    water_day = Period.of("P1D+T9H")

    assert water_day.has_offset() == True
    assert water_day.month_offset == 0
    assert water_day.microsecond_offset == 9 * 3_600 * 1_000_000
    assert water_day.offset == "+T32400S"
    assert water_day.iso_duration == "P1D"  # the duration alone, without the offset
    assert str(water_day) == "P1D+T9H"      # gives duration and offset together

Setting an origin
=================

:meth:`~isoperiod.Period.with_origin` makes a chosen datetime ordinal ``0`` **and** an interval boundary. It is
what you need for a period with no meaningful natural boundary - e.g. a 7-day period, or an instrument started at an
arbitrary time:

.. code-block:: python

    p = Period.of_days(7).with_origin(datetime(2024, 1, 1))

    assert p.ordinal(datetime(2024, 1, 1)) == 0
    assert p.is_aligned(datetime(2024, 1, 1)) == True
    assert p.datetime(1) == datetime(2024, 1, 8)
    assert p.datetime(-1) == datetime(2023, 12, 25)

The ``<start>/<duration>`` string format does the same thing:

.. code-block:: python

    assert Period.of("2024-01-01/P7D") == Period.of_days(7).with_origin(datetime(2024, 1, 1))

An origin discards any offset already on the period and recomputes it from the origin datetime. If the origin carries a
:class:`~datetime.tzinfo`, the resulting period adopts it.

Removing offsets and origins
============================

Three methods remove the modifications, each returning a new period:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Method
     - Removes
   * - :meth:`~isoperiod.Period.without_offset`
     - the date/time offset, keeping the ordinal numbering
   * - :meth:`~isoperiod.Period.without_ordinal_shift`
     - the origin's numbering, keeping the boundaries
   * - :meth:`~isoperiod.Period.base_period`
     - both - back to the plain period the factories produce

.. code-block:: python

    p = Period.of("2024-01-01/P7D")

    assert p.base_period() == Period.of_days(7)
    assert Period.of("P1D+T9H").base_period() == Period.of_days(1)

    # The boundaries are unchanged; only the numbering is.
    q = p.without_ordinal_shift()
    assert q.is_aligned(datetime(2024, 1, 1)) == True
    assert q.ordinal(datetime(2024, 1, 1)) != 0
