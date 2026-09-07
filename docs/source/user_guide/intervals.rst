.. _intervals_and_ordinals:

======================
Intervals and ordinals
======================

.. rst-class:: lead

    Mapping between datetimes and the intervals that contain them.

A period splits the timeline into consecutive intervals and numbers them with integers called *ordinals*. Two
methods move between the two views, and they are inverses of each other:

.. code-block:: python

    from datetime import datetime, timedelta
    from isoperiod import Period

    p1h = Period.of_hours(1)
    d = datetime(2024, 3, 1, 9, 47)

    n = p1h.ordinal(d)                                  # datetime -> interval number
    assert p1h.datetime(n) == datetime(2024, 3, 1, 9)  # interval number -> first instant

Flooring a timestamp to its interval
====================================

Round-tripping through an ordinal floors a datetime onto the period's grid. This also works for calendar units where
arithmetic on a ``timedelta`` cannot:

.. code-block:: python

    def floor(period: Period, d: datetime) -> datetime:
        """The start of the interval containing `d`."""
        return period.datetime(period.ordinal(d))

    d = datetime(2024, 3, 15, 9, 47, 30)

    assert floor(Period.of_minutes(15), d) == datetime(2024, 3, 15, 9, 45)
    assert floor(Period.of_days(1), d) == datetime(2024, 3, 15)
    assert floor(Period.of_months(1), d) == datetime(2024, 3, 1)
    assert floor(Period.of_years(1), d) == datetime(2024, 1, 1)


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

To generate the boundaries between two datetimes, iterate over the ordinal range:

.. code-block:: python

    def boundaries(period: Period, start: datetime, end: datetime) -> list[datetime]:
        """Every interval start from the one containing `start` up to (not including) `end`."""
        return [
            period.datetime(n)
            for n in range(period.ordinal(start), period.ordinal(end) + 1)
            if period.datetime(n) < end
        ]

    assert boundaries(Period.of_hours(6), datetime(2024, 3, 1), datetime(2024, 3, 2)) == [
        datetime(2024, 3, 1, 0),
        datetime(2024, 3, 1, 6),
        datetime(2024, 3, 1, 12),
        datetime(2024, 3, 1, 18),
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
