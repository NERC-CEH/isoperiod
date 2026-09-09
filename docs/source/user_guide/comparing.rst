.. _comparing_periods:

=================
Comparing periods
=================

.. rst-class:: lead

    Equality, ordering, and the two questions about how one period nests inside another.

Equality, hashing and sorting
=============================

Periods are immutable and hashable, so they work as dict keys and set members.

Two periods are equal when they split the timeline the same way and number it the same way - the way they were built
is irrelevant:

.. literalinclude:: ../examples/comparing.py
   :language: python
   :start-after: [start:equality]
   :end-before: [end:equality]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import comparing

   comparing.equality()

Periods also sort, shortest first - including across the boundary between calendar and fixed-length periods:

.. literalinclude:: ../examples/comparing.py
   :language: python
   :start-after: [start:sorting]
   :end-before: [end:sorting]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import comparing

   comparing.sorting()

.. note::

   A calendar month has no fixed length, so ordering takes it as its mean Gregorian length of 30.436875 days
   (365.2425 / 12). That approximation is used *only* to order periods.

.. note::

   Sorting periods with mismatched :class:`~datetime.tzinfo` values raises :class:`TypeError`, exactly as sorting
   naive and aware datetimes does. Equality is safe in all cases - a period with a timezone is never equal to one
   without. See :doc:`timezones`.

Counting one period inside another
==================================

:meth:`~isoperiod.Period.count` returns how many intervals of one period fit into each interval of another. A
count exists when the smaller period's intervals fill the larger one exactly - one starts where the larger
interval starts, another ends where it ends, and no part-intervals fall in between.

.. literalinclude:: ../examples/comparing.py
   :language: python
   :start-after: [start:counting]
   :end-before: [end:counting]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import comparing

   comparing.counting()

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

.. literalinclude:: ../examples/comparing.py
   :language: python
   :start-after: [start:counting_without_an_answer]
   :end-before: [end:counting_without_an_answer]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import comparing

   comparing.counting_without_an_answer()

To tell the two ``None`` cases apart, ask :meth:`~isoperiod.Period.is_subperiod_of`, below - it is True for the
first and False for the second.

Offsets are taken into account. What matters is not that the offsets are *equal*, but that they differ by a whole
number of the smaller period - that is what makes every boundary of the larger land on a boundary of the smaller:

.. literalinclude:: ../examples/comparing.py
   :language: python
   :start-after: [start:counting_with_offsets]
   :end-before: [end:counting_with_offsets]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import comparing

   comparing.counting_with_offsets()

Testing containment
===================

:meth:`~isoperiod.Period.is_subperiod_of` asks the question: does every interval of this period fall wholly
inside a single interval of the other, never straddling a boundary?

.. literalinclude:: ../examples/comparing.py
   :language: python
   :start-after: [start:containment]
   :end-before: [end:containment]
   :dedent:

**Which to use:** :meth:`~isoperiod.Period.is_subperiod_of` when you need to know that aggregating is *safe*;
:meth:`~isoperiod.Period.count` when you also need to know *how many* values to expect - for example to report
completeness.

Epoch agnosticism
=================

:meth:`~isoperiod.Period.is_epoch_agnostic` says whether a period splits the timeline the same way regardless of
where counting begins. A period is epoch agnostic when its length divides evenly into the fixed unit above it - a
day for clock periods, a year for calendar ones:

.. literalinclude:: ../examples/comparing.py
   :language: python
   :start-after: [start:epoch_agnosticism]
   :end-before: [end:epoch_agnosticism]
   :dedent:

**Why it matters:** an epoch-agnostic period is safe to publish on its own - anybody reading ``"PT15M"`` will
place the boundaries where you did. A period that is not needs an explicit origin to be unambiguous, so exchange
it as ``"2024-01-01/P7D"`` rather than ``"P7D"``. See :doc:`offsets`.

.. note::

   An origin does not change the answer. :meth:`~isoperiod.Period.is_epoch_agnostic` reports on the period's
   length alone, and ``2024-01-01/P7D`` splits the timeline exactly as ``P7D+1D`` does - the origin only fixes
   which interval is numbered zero:

   .. literalinclude:: ../examples/comparing.py
      :language: python
      :start-after: [start:an_origin_does_not_change_it]
      :end-before: [end:an_origin_does_not_change_it]
      :dedent:

   .. jupyter-execute::
      :hide-code:

      from examples import comparing

      comparing.an_origin_does_not_change_it()
