.. _creating_periods:

================
Creating periods
================

.. rst-class:: lead

    Every way to build a :class:`~isoperiod.Period`, and what each one means.

:class:`~isoperiod.Period` is abstract - you never instantiate it directly. Instead, a set of static factory
methods are available to build a period in various ways. All of them return a fully-formed period.

From a named unit
=================

The most direct route. Each factory takes a count of that unit:

.. list-table::
   :header-rows: 1
   :widths: 20 30 35

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

.. literalinclude:: ../examples/creating.py
   :language: python
   :start-after: [start:plain_iso_durations]
   :end-before: [end:plain_iso_durations]
   :dedent:

Components combine, and the period renders back as the string that built it:

.. literalinclude:: ../examples/creating.py
   :language: python
   :start-after: [start:combining_components]
   :end-before: [end:combining_components]
   :dedent:

.. warning::

   A period cannot mix calendar units (years, months) with clock units (days and below), because months have no
   fixed length in seconds. ``"P1M1D"`` raises :class:`~isoperiod.PeriodValidationError`.

.. note::

   :meth:`~isoperiod.Period.of_iso_duration` parses this form and only this form - useful when you want to reject the
   extended syntaxes explicitly.

2. Duration with an offset
--------------------------

An extension of the ISO 8601 format, written ``<duration>+<offset>``. The offset is itself a duration, and shifts
every interval boundary forwards by that amount:

.. literalinclude:: ../examples/creating.py
   :language: python
   :start-after: [start:offset_form]
   :end-before: [end:offset_form]
   :dedent:

There are also ``with_*_offset`` methods that apply an offset to an existing period (returning a new independent Period
object):

.. literalinclude:: ../examples/creating.py
   :language: python
   :start-after: [start:with_offset_form]
   :end-before: [end:with_offset_form]
   :dedent:

.. note::

    :meth:`~isoperiod.Period.of_duration` accepts both this offset form and a plain duration (with no offset).

3. Duration with an origin
--------------------------

Written ``<start>/<duration>``. The ``start`` datetime becomes ordinal ``0`` **and** a boundary of the period, which
fixes the grid for periods that have no meaningful natural boundary:

.. literalinclude:: ../examples/creating.py
   :language: python
   :start-after: [start:origin_form]
   :end-before: [end:origin_form]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import creating

   creating.origin_form()

The start may be a full datetime, or a reduced-precision date - a bare year or year-month is padded to its first
instant, following ISO 8601:

.. literalinclude:: ../examples/creating.py
   :language: python
   :start-after: [start:reduced_precision_origin]
   :end-before: [end:reduced_precision_origin]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import creating

   creating.reduced_precision_origin()


.. note::

   :meth:`~isoperiod.Period.of_date_and_duration` parses this form only.

From a timedelta
================

:meth:`~isoperiod.Period.of_timedelta` builds a period matching any fixed-length duration:

.. literalinclude:: ../examples/creating.py
   :language: python
   :start-after: [start:from_timedelta]
   :end-before: [end:from_timedelta]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import creating

   creating.from_timedelta()

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

.. literalinclude:: ../examples/creating.py
   :language: python
   :start-after: [start:handling_bad_input]
   :end-before: [end:handling_bad_input]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import creating

   creating.handling_bad_input()
