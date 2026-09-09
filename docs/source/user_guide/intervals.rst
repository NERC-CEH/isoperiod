.. _intervals_and_ordinals:

======================
Intervals and ordinals
======================

.. rst-class:: lead

    Mapping between datetimes and the intervals that contain them.

Ordinals
========

A period splits the timeline into consecutive intervals and numbers them with integers called *ordinals*. Two
methods move between the two views, and they are inverses of each other:

.. literalinclude:: ../examples/intervals.py
   :language: python
   :start-after: [start:ordinal_and_datetime]
   :end-before: [end:ordinal_and_datetime]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import intervals

   intervals.ordinal_and_datetime()

Flooring a timestamp to its interval
====================================

:meth:`~isoperiod.Period.floor` snaps a datetime down onto the period's grid. This also works for calendar units
where arithmetic on a ``timedelta`` cannot:

.. literalinclude:: ../examples/intervals.py
   :language: python
   :start-after: [start:flooring]
   :end-before: [end:flooring]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import intervals

   intervals.flooring()

An offset moves every boundary, and with it what a timestamp floors to:

.. literalinclude:: ../examples/intervals.py
   :language: python
   :start-after: [start:flooring_with_offset]
   :end-before: [end:flooring_with_offset]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import intervals

   intervals.flooring_with_offset()

Stepping along the timeline
===========================

Adding to an ordinal moves whole intervals, whatever their calendar length. This is how to walk a monthly or
yearly grid without worrying about month ends:

.. literalinclude:: ../examples/intervals.py
   :language: python
   :start-after: [start:stepping]
   :end-before: [end:stepping]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import intervals

   intervals.stepping()

:meth:`~isoperiod.Period.range` does that walk for you, yielding the start of every interval that overlaps a
window of time:

.. literalinclude:: ../examples/intervals.py
   :language: python
   :start-after: [start:walking_a_window]
   :end-before: [end:walking_a_window]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import intervals

   intervals.walking_a_window()

An interval counts as overlapping if any part of it falls in the window, so a window opening part-way through an
interval still yields the whole of it. This is usually what you want when deciding which intervals a batch of
readings touches:

.. literalinclude:: ../examples/intervals.py
   :language: python
   :start-after: [start:walking_a_partial_window]
   :end-before: [end:walking_a_partial_window]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import intervals

   intervals.walking_a_partial_window()

Values are produced lazily, so a window covering a large number of intervals costs nothing until it is iterated.

Bounding a single interval
==========================

:meth:`~isoperiod.Period.interval` returns the start and end of the interval holding a datetime, as a half-open
pair - `end` is the first instant of the next interval, so ``start <= d < end`` holds for every datetime in it:

.. literalinclude:: ../examples/intervals.py
   :language: python
   :start-after: [start:bounding_an_interval]
   :end-before: [end:bounding_an_interval]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import intervals

   intervals.bounding_an_interval()

The start is the same value :meth:`~isoperiod.Period.floor` gives; the end is the new information, and it is the
part you cannot get by adding a ``timedelta`` when the period is a calendar one.

Since :meth:`~isoperiod.Period.range` yields datetimes, the two can be used together to walk a window as bounded
intervals:

.. literalinclude:: ../examples/intervals.py
   :language: python
   :start-after: [start:walking_bounded_intervals]
   :end-before: [end:walking_bounded_intervals]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import intervals

   intervals.walking_bounded_intervals()

Grouping by interval
====================

Two datetimes share an ordinal exactly when they fall in the same interval, so the start of that interval makes a
natural grouping key:

.. literalinclude:: ../examples/intervals.py
   :language: python
   :start-after: [start:grouping]
   :end-before: [end:grouping]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import intervals

   intervals.grouping()

Checking alignment
==================

:meth:`~isoperiod.Period.is_aligned` tests whether a datetime falls exactly on an interval boundary - the check to
run on incoming data before trusting its claimed resolution:

.. literalinclude:: ../examples/intervals.py
   :language: python
   :start-after: [start:alignment]
   :end-before: [end:alignment]
   :dedent:

Offsets move the boundaries, and with them what counts as aligned:

.. literalinclude:: ../examples/intervals.py
   :language: python
   :start-after: [start:alignment_with_offset]
   :end-before: [end:alignment_with_offset]
   :dedent:

What an ordinal actually is
===========================

For the common periods, ordinals turn out to be quantities you may already recognise - the year, the number of
months since year 0, and the proleptic Gregorian day ordinal:

.. literalinclude:: ../examples/intervals.py
   :language: python
   :start-after: [start:what_an_ordinal_is]
   :end-before: [end:what_an_ordinal_is]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import intervals

   intervals.what_an_ordinal_is()

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
:attr:`~isoperiod.Period.min_ordinal` and :attr:`~isoperiod.Period.max_ordinal` give the usable range.

.. literalinclude:: ../examples/intervals.py
   :language: python
   :start-after: [start:ends_of_the_timeline]
   :end-before: [end:ends_of_the_timeline]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import intervals

   intervals.ends_of_the_timeline()

Going outside out these bounds raises :class:`ValueError` from :mod:`datetime` itself:

.. literalinclude:: ../examples/intervals.py
   :language: python
   :start-after: [start:ends_of_the_timeline_error]
   :end-before: [end:ends_of_the_timeline_error]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import intervals

   intervals.ends_of_the_timeline_error()
