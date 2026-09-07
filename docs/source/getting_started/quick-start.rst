.. _quick-start:

===========
Quick start
===========

.. rst-class:: lead

    A five-minute tour of **isoperiod**. Each section links to the user guide page that covers it properly.

.. code-block:: python

    from datetime import datetime
    from isoperiod import Period

Build a period
==============

Either from an ISO 8601 duration string, or from a named unit:

.. code-block:: python

    p15min = Period.of("PT15M")
    p1d = Period.of_days(1)
    p1m = Period.of_months(1)

    assert p15min.iso_duration == "PT15M"

Periods that describe the same grid are equal, however you spell them:

.. code-block:: python

    assert Period.of_hours(24) == Period.of_days(1)
    assert Period.of_months(12) == Period.of_years(1)

See :doc:`/user_guide/creating` for every factory, all three string formats, and error handling.

Find the interval a timestamp falls in
======================================

:meth:`~isoperiod.Period.ordinal` gives the number of the interval containing a datetime;
:meth:`~isoperiod.Period.datetime` turns that number back into the interval's first instant. Together they floor a
timestamp onto the grid:

.. code-block:: python

    reading = datetime(2024, 3, 15, 9, 47, 30)

    n = p15min.ordinal(reading)
    assert p15min.datetime(n) == datetime(2024, 3, 15, 9, 45)      # this interval
    assert p15min.datetime(n + 1) == datetime(2024, 3, 15, 10, 0)  # the next one

It works just as well for calendar units, which no ``timedelta`` can express:

.. code-block:: python

    n = p1m.ordinal(reading)
    assert p1m.datetime(n) == datetime(2024, 3, 1)
    assert p1m.datetime(n + 1) == datetime(2024, 4, 1)

See :doc:`/user_guide/intervals` for stepping along the timeline, grouping by interval, and generating boundaries.

Check that data sits on the grid
================================

:meth:`~isoperiod.Period.is_aligned` answers "is this timestamp exactly on a boundary?":

.. code-block:: python

    assert Period.of_hours(1).is_aligned(datetime(2024, 3, 15, 9, 0)) == True
    assert Period.of_hours(1).is_aligned(datetime(2024, 3, 15, 9, 47)) == False

Use an offset for a non-standard boundary
=========================================

An offset moves every boundary of the period by a fixed amount - which is how a hydrological day, running 09:00 to
09:00, is expressed:

.. code-block:: python

    p_water_day = Period.of_days(1).with_hour_offset(9)
    assert p_water_day == Period.of("P1D+T9H")   # the same period, written as a string

    # 07:30 belongs to the water day that began at 09:00 the previous day.
    reading = datetime(2024, 3, 15, 7, 30)
    assert p_water_day.datetime(p_water_day.ordinal(reading)) == datetime(2024, 3, 14, 9, 0)

See :doc:`/user_guide/offsets` for the full set of offset builders, the water year, and pinning a grid to an origin.

Compare two periods
===================

Ask how one period nests inside another:

.. code-block:: python

    assert p15min.count(Period.of("PT1H")) == 4
    assert p15min.count(p1d) == 96

    # None when there is no single answer - here because months hold 28-31 days.
    assert p1d.count(p1m) is None
    assert p1d.is_subperiod_of(p1m) == True

See :doc:`/user_guide/comparing` for the two cases that give ``None``, offsets, and epoch agnosticism.

Where next
==========

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Page
     - Covers
   * - :doc:`concepts`
     - The ideas behind the API: intervals, ordinals, offsets, origins, alignment
   * - :doc:`/user_guide/creating`
     - Every way to build a period, and what each string format means
   * - :doc:`/user_guide/intervals`
     - Flooring, stepping, grouping, alignment, the ends of the timeline
   * - :doc:`/user_guide/offsets`
     - Offsets and origins, worked hydrological examples, stripping them off again
   * - :doc:`/user_guide/comparing`
     - Equality, ordering, counting, containment, epoch agnosticism
   * - :doc:`/user_guide/timezones`
     - What a period's tzinfo does, and what it deliberately does not
   * - :doc:`/user_guide/interop`
     - String forms, ``timedelta`` conversion, Polars duration strings
   * - :doc:`/api/period`
     - The full :class:`~isoperiod.Period` reference
