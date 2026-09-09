.. _quick-start:

===========
Quick start
===========

.. rst-class:: lead

    A five-minute tour of **isoperiod**. Each section links to the user guide page that covers it properly.

Build a period
==============

Either from an ISO 8601 duration string, or from a named unit:

.. literalinclude:: ../examples/quick_start.py
   :language: python
   :start-after: [start:build_a_period]
   :end-before: [end:build_a_period]
   :dedent:

Periods that describe the same grid are equal, however you spell them:

.. literalinclude:: ../examples/quick_start.py
   :language: python
   :start-after: [start:equal_periods]
   :end-before: [end:equal_periods]
   :dedent:

See :doc:`/user_guide/creating` for every factory, all three string formats, and error handling.

Find the interval a timestamp falls in
======================================

:meth:`~isoperiod.Period.ordinal` gives the number of the interval containing a datetime;
:meth:`~isoperiod.Period.datetime` turns that ordinal number back into the interval's first instant.

Together they floor a timestamp onto the grid:

.. literalinclude:: ../examples/quick_start.py
   :language: python
   :start-after: [start:find_the_interval]
   :end-before: [end:find_the_interval]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import quick_start

   quick_start.find_the_interval()

When only the start boundary is wanted, :meth:`~isoperiod.Period.floor` performs that in one call:

.. literalinclude:: ../examples/quick_start.py
   :language: python
   :start-after: [start:flooring]
   :end-before: [end:flooring]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import quick_start

   quick_start.flooring()

Additionally, :meth:`~isoperiod.Period.interval` provides a way to get both the start and end boundary of a period in
one call:

.. literalinclude:: ../examples/quick_start.py
   :language: python
   :start-after: [start:interval]
   :end-before: [end:interval]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import quick_start

   quick_start.interval()

See :doc:`/user_guide/intervals` for stepping along the timeline, grouping by interval, and generating boundaries.

Check that data sits on the grid
================================

:meth:`~isoperiod.Period.is_aligned` answers "is this timestamp exactly on a boundary?":

.. literalinclude:: ../examples/quick_start.py
   :language: python
   :start-after: [start:check_alignment]
   :end-before: [end:check_alignment]
   :dedent:

Use an offset for a non-standard boundary
=========================================

An offset moves every boundary of the period by a fixed amount. For example, we can express a hydrological day,
which runs from 09:00 to 09:00, using an offset:

.. literalinclude:: ../examples/quick_start.py
   :language: python
   :start-after: [start:use_an_offset]
   :end-before: [end:use_an_offset]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import quick_start

   quick_start.use_an_offset()

See :doc:`/user_guide/offsets` for the full set of offset builders, the water year, and pinning a grid to an origin.

Compare two periods
===================

The :meth:`~isoperiod.Period.count` method gives a way to explore how one period nests inside another:

.. literalinclude:: ../examples/quick_start.py
   :language: python
   :start-after: [start:compare_periods]
   :end-before: [end:compare_periods]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import quick_start

   quick_start.compare_periods()

See :doc:`/user_guide/comparing` for more detail, include special cases, how offsets work with comparisons, and epoch
agnosticism.

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
