.. _comparing_periods:

=================
Comparing periods
=================

.. rst-class:: lead

    Equality, ordering, and the two questions about how one period nests inside another.

.. code-block:: python

    from datetime import datetime
    from isoperiod import Period

Equality, hashing and sorting
=============================

Periods are immutable and hashable, so they work as dict keys and set members. Two periods are equal when they
split the timeline the same way and number it the same way - the way they were built is irrelevant:

.. code-block:: python

    assert Period.of_hours(24) == Period.of_days(1)
    assert Period.of("PT15M") == Period.of_minutes(15) == Period.of_seconds(900)

Periods also sort, shortest first:

.. code-block:: python

    periods = [Period.of_years(1), Period.of_hours(1), Period.of_days(1), Period.of_months(1)]

    assert sorted(periods) == [
        Period.of_hours(1),
        Period.of_days(1),
        Period.of_months(1),
        Period.of_years(1)
    ]

.. note::

   Sorting periods with mismatched :class:`~datetime.tzinfo` values raises :class:`TypeError`, exactly as sorting
   naive and aware datetimes does. Equality is safe in all cases - a period with a timezone is never equal to one
   without. See :doc:`timezones`.

Counting one period inside another
==================================

:meth:`~isoperiod.Period.count` returns how many intervals of one period fit into each interval of another. A
count exists when the smaller period's intervals fill the larger one exactly - one starts where the larger
interval starts, another ends where it ends, and no part-intervals fall in between.

.. code-block:: python

    p15m = Period.of_minutes(15)
    p1h = Period.of_hours(1)
    p1d = Period.of_days(1)
    p1m = Period.of_months(1)
    p1y = Period.of_years(1)

    assert p15m.count(p1h) == 4
    assert p1h.count(p1d) == 24
    assert p1m.count(p1y) == 12

Two situations have no such number. Both return ``None`` rather than raising, because asking is legitimate and
the answer "there isn't one" is a real answer:

.. list-table::
   :header-rows: 1

   * - Case
     - Example
   * - aligned, but the count varies
     - days in a month - clean boundaries, 28 to 31 of them
   * - not aligned, or this period is the larger
     - 15 minutes offset by 5 against a plain hour

.. code-block:: python

    assert p1d.count(p1m) is None                    # aligned, but months hold 28-31 days
    assert p1d.count(p1h) is None                    # the larger never fits inside the smaller
    assert Period.of_minutes(25).count(p1h) is None  # 60 is not a multiple of 25

To tell the two ``None`` cases apart, ask :meth:`~isoperiod.Period.is_subperiod_of`, below - it is True for the
first and False for the second.

Offsets are taken into account. What matters is not that the offsets are *equal*, but that they differ by a whole
number of the smaller period - that is what makes every boundary of the larger land on a boundary of the smaller:

.. code-block:: python

    assert Period.of("PT15M+T5M").count(p1h) is None                  # :05 :20 :35 :50 straddle the hour
    assert Period.of("PT15M+T5M").count(Period.of("PT1H+T5M")) == 4   # both offset alike
    assert Period.of("PT15M+T5M").count(Period.of("PT1H+T20M")) == 4  # offsets differ by one 15-min step

Testing containment
===================

:meth:`~isoperiod.Period.is_subperiod_of` asks the question: does every interval of this period fall wholly
inside a single interval of the other, never straddling a boundary?

.. code-block:: python

    assert p1h.is_subperiod_of(p1d) == True  # an hour never straddles midnight
    assert p1d.is_subperiod_of(p1m) == True  # nor a day a month boundary, despite varying month lengths
    assert p15m.is_subperiod_of(p1h) == True

    assert p1d.is_subperiod_of(p1h) == False  # the larger is never contained by the smaller
    assert Period.of("PT15M+T5M").is_subperiod_of(p1h) == False

    assert p1d.is_subperiod_of(p1d) == True  # a period always contains itself

**Which to use:** :meth:`~isoperiod.Period.is_subperiod_of` when you need to know that aggregating is *safe*;
:meth:`~isoperiod.Period.count` when you also need to know *how many* values to expect - for example to report
completeness.

Epoch agnosticism
=================

:meth:`~isoperiod.Period.is_epoch_agnostic` says whether a period splits the timeline the same way regardless of
where counting begins. A period is epoch agnostic when its length divides evenly into the fixed unit above it - a
day for clock periods, a year for calendar ones:

.. code-block:: python

    assert Period.of_minutes(15).is_epoch_agnostic() == True  # 15 minutes divides into a day
    assert Period.of_hours(6).is_epoch_agnostic() == True
    assert Period.of_days(1).is_epoch_agnostic() == True
    assert Period.of_months(3).is_epoch_agnostic() == True    # 3 months divides into a year

    assert Period.of_days(7).is_epoch_agnostic() == False  # which 7 days? depends where you start
    assert Period.of_minutes(7).is_epoch_agnostic() == False
    assert Period.of_months(5).is_epoch_agnostic() == False

**Why it matters:** an epoch-agnostic period is safe to publish on its own - anybody reading ``"PT15M"`` will
place the boundaries where you did. A period that is not needs an explicit origin to be unambiguous, so exchange
it as ``"2024-01-01/P7D"`` rather than ``"P7D"``. See :doc:`offsets`.

.. note::

   An origin does not change the answer. :meth:`~isoperiod.Period.is_epoch_agnostic` reports on the period's
   length alone, and ``2024-01-01/P7D`` splits the timeline exactly as ``P7D+1D`` does - the origin only fixes
   which interval is numbered zero:

   .. code-block:: python

       assert Period.of("2024-01-01/P7D").is_epoch_agnostic() == False
       assert Period.of("2024-01-01/P7D").without_ordinal_shift() == Period.of("P7D+1D")
