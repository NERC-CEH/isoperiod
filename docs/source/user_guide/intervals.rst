.. _intervals_and_ordinals:

======================
Intervals and ordinals
======================

.. rst-class:: lead

    Mapping between datetimes and the intervals that contain them.

A period splits the timeline into consecutive intervals and numbers them with integers called *ordinals*. Two
methods move between the two views, and they are inverses of each other:

.. code-block:: python

    from datetime import datetime
    from isoperiod import Period

    p1h = Period.of_hours(1)
    d = datetime(2024, 3, 1, 9, 47)

    n = p1h.ordinal(d)                                  # datetime -> interval number
    assert p1h.datetime(n) == datetime(2024, 3, 1, 9)  # interval number -> first instant

Flooring a timestamp to its interval
====================================

:meth:`~isoperiod.Period.floor` snaps a datetime down onto the period's grid. This also works for calendar units
where arithmetic on a ``timedelta`` cannot:

.. code-block:: python

    d = datetime(2024, 3, 15, 9, 47, 30)

    assert Period.of_minutes(15).floor(d) == datetime(2024, 3, 15, 9, 45)
    assert Period.of_days(1).floor(d) == datetime(2024, 3, 15)
    assert Period.of_months(1).floor(d) == datetime(2024, 3, 1)
    assert Period.of_years(1).floor(d) == datetime(2024, 1, 1)

An offset moves every boundary, and with it what a timestamp floors to:

.. code-block:: python

    assert Period.of("P1D+T9H").floor(datetime(2024, 3, 15, 7, 30)) == datetime(2024, 3, 14, 9, 0)


Stepping along the timeline
===========================

Adding to an ordinal moves whole intervals, whatever their calendar length. This is how to walk a monthly or
yearly grid without worrying about month ends:

.. code-block:: python

    p1m = Period.of_months(1)
    n = p1m.ordinal(datetime(2024, 1, 31))

    starts = [p1m.datetime(n + i) for i in range(4)]
    assert starts == [
        datetime(2024, 1, 1),
        datetime(2024, 2, 1),
        datetime(2024, 3, 1),
        datetime(2024, 4, 1),
    ]

:meth:`~isoperiod.Period.range` does that walk for you, yielding the start of every interval that overlaps a
window of time:

.. code-block:: python

    pt6h = Period.of_hours(6)


    window_start = datetime(2024, 3, 1)
    window_end = datetime(2024, 3, 2)

    # Create a generator that steps through the start of each "pt6h" period in the window
    window_range = pt6h.range(window_start, window_end)

    assert list(window_range) == [
        datetime(2024, 3, 1, 0),
        datetime(2024, 3, 1, 6),
        datetime(2024, 3, 1, 12),
        datetime(2024, 3, 1, 18),
    ]

An interval counts as overlapping if any part of it falls in the window, so a window opening part-way through an
interval still yields the whole of it. This is usually what you want when deciding which intervals a batch of
readings touches:

.. code-block:: python

    pt6h = Period.of_hours(6)

    window_start = datetime(2024, 3, 1, 3)
    window_end = datetime(2024, 3, 1, 13)

    window_range = pt6h.range(window_start, window_end)

    assert list(window_range) == [
        datetime(2024, 3, 1, 0),
        datetime(2024, 3, 1, 6),
        datetime(2024, 3, 1, 12),
    ]

Values are produced lazily, so a window covering a large number of intervals costs nothing until it is iterated.

Bounding a single interval
==========================

:meth:`~isoperiod.Period.interval` returns the start and end of the interval holding a datetime, as a half-open
pair - `end` is the first instant of the next interval, so ``start <= d < end`` holds for every datetime in it:

.. code-block:: python

    pt1h = Period.of_hours(1)
    d = datetime(2024, 3, 15, 9, 47)

    start, end = pt1h.interval(d)

    assert (start, end) == (datetime(2024, 3, 15, 9), datetime(2024, 3, 15, 10))

The start is the same value :meth:`~isoperiod.Period.floor` gives; the end is the new information, and it is the
part you cannot get by adding a ``timedelta`` when the period is a calendar one.

Since :meth:`~isoperiod.Period.range` yields datetimes, the two can be used together to walk a window as bounded
intervals:

.. code-block:: python

    spans = [pt6h.interval(s) for s in pt6h.range(datetime(2024, 3, 1), datetime(2024, 3, 1, 13))]

    assert spans == [
        (datetime(2024, 3, 1, 0), datetime(2024, 3, 1, 6)),
        (datetime(2024, 3, 1, 6), datetime(2024, 3, 1, 12)),
        (datetime(2024, 3, 1, 12), datetime(2024, 3, 1, 18)),
    ]


Grouping by interval
====================

Two datetimes share an ordinal exactly when they fall in the same interval, so an ordinal makes a natural grouping
key:

.. code-block:: python

    readings = {
        datetime(2024, 3, 15, 9, 47): 1.2,
        datetime(2024, 3, 15, 9, 52): 1.4,
        datetime(2024, 3, 15, 10, 3): 1.1,
    }

    p = Period.of_hours(1)
    hourly: dict[datetime, list[float]] = {}
    for when, value in readings.items():
        hourly.setdefault(p.datetime(p.ordinal(when)), []).append(value)

    assert hourly == {
        datetime(2024, 3, 15, 9): [1.2, 1.4],
        datetime(2024, 3, 15, 10): [1.1],
    }

Checking alignment
==================

:meth:`~isoperiod.Period.is_aligned` tests whether a datetime falls exactly on an interval boundary - the check to
run on incoming data before trusting its claimed resolution:

.. code-block:: python

    p15m = Period.of_minutes(15)

    assert p15m.is_aligned(datetime(2024, 3, 15, 9, 45)) == True
    assert p15m.is_aligned(datetime(2024, 3, 15, 9, 47)) == False

Offsets move the boundaries, and with them what counts as aligned:

.. code-block:: python

    water_day = Period.of("P1D+T9H")

    assert water_day.is_aligned(datetime(2024, 3, 15, 9, 0)) == True
    assert water_day.is_aligned(datetime(2024, 3, 15, 0, 0)) == False

What an ordinal actually is
===========================

For the common periods, ordinals turn out to be quantities you may already recognise:

.. code-block:: python

    assert Period.of_years(1).ordinal(datetime(2024, 7, 1)) == 2024            # the year
    assert Period.of_months(1).ordinal(datetime(2024, 3, 1)) == 2024 * 12 + 2  # months since year 0
    assert Period.of_days(1).ordinal(datetime(2024, 3, 15)) == datetime(2024, 3, 15).toordinal()

That is incidental, though - the guarantees are only that ordinals are consecutive integers, and that
:meth:`~isoperiod.Period.ordinal` and :meth:`~isoperiod.Period.datetime` invert each other. Do not persist ordinals
or send them between systems; store the datetime and re-derive the ordinal.

.. warning::

   An ordinal is only meaningful to the period that produced it. Each period numbers the timeline in its own
   units, so passing one period's ordinal to another period's :meth:`~isoperiod.Period.datetime` would not be
   meaningful.

The ends of the timeline
========================

Ordinals are unbounded integers, but :class:`~datetime.datetime` only covers years 1 to 9999.
:attr:`~isoperiod.Period.min_ordinal` and :attr:`~isoperiod.Period.max_ordinal` give the usable range:

.. code-block:: python

    p1y = Period.of_years(1)

    assert p1y.min_ordinal == 1
    assert p1y.max_ordinal == 9999
    assert p1y.datetime(p1y.min_ordinal) == datetime(1, 1, 1)

Going outside that range raises :class:`ValueError` from :mod:`datetime` itself:

.. code-block:: python

    try:
        Period.of_days(1).datetime(10 ** 9)
    except ValueError as err:
        print(err)     # year 2737908 is out of range
