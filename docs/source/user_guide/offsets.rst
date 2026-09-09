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
    *Where are the boundaries?* Shifts every boundary by a fixed amount, keeping the interval size.

**Origin**
    *Which interval is number zero?* Pins the numbering to a chosen datetime, and aligns the boundaries so that
    datetime is one of them.

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

.. literalinclude:: ../examples/offsets.py
   :language: python
   :start-after: [start:hydrological_day]
   :end-before: [end:hydrological_day]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import offsets

   offsets.hydrological_day()

Alignment follows the shifted boundaries:

.. literalinclude:: ../examples/offsets.py
   :language: python
   :start-after: [start:hydrological_day_alignment]
   :end-before: [end:hydrological_day_alignment]
   :dedent:

Worked example: the water year
==============================

The UK water year runs from 09:00 on 1 October. That is a one-year period offset by nine months and nine hours:

.. literalinclude:: ../examples/offsets.py
   :language: python
   :start-after: [start:water_year]
   :end-before: [end:water_year]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import offsets

   offsets.water_year()

Offsets are accounted for when periods are compared, so a hydrological day nests cleanly inside a water year -
while a calendar day, which straddles the 09:00 boundary every 1 October, does not:

.. literalinclude:: ../examples/offsets.py
   :language: python
   :start-after: [start:offsets_when_comparing]
   :end-before: [end:offsets_when_comparing]
   :dedent:

See :doc:`comparing` for the full rules.

Inspecting an offset
====================

.. literalinclude:: ../examples/offsets.py
   :language: python
   :start-after: [start:inspecting_an_offset]
   :end-before: [end:inspecting_an_offset]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import offsets

   offsets.inspecting_an_offset()

Setting an origin
=================

:meth:`~isoperiod.Period.with_origin` makes a chosen datetime ordinal ``0`` **and** an interval boundary. It is
what you need for a period with no meaningful natural boundary - e.g. a 7-day period, or an instrument started at an
arbitrary time:

.. literalinclude:: ../examples/offsets.py
   :language: python
   :start-after: [start:setting_an_origin]
   :end-before: [end:setting_an_origin]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import offsets

   offsets.setting_an_origin()

The ``<start>/<duration>`` string format does the same thing:

.. literalinclude:: ../examples/offsets.py
   :language: python
   :start-after: [start:origin_from_a_string]
   :end-before: [end:origin_from_a_string]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import offsets

   offsets.origin_from_a_string()

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

.. literalinclude:: ../examples/offsets.py
   :language: python
   :start-after: [start:removing_offsets_and_origins]
   :end-before: [end:removing_offsets_and_origins]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import offsets

   offsets.removing_offsets_and_origins()
