.. _timezones:

==========
Time zones
==========

.. rst-class:: lead

    A period's timezone is a label on the clock it counts, not a conversion.

A period can carry a :class:`~datetime.tzinfo`, set with :meth:`~isoperiod.Period.with_tzinfo`:

The tzinfo does three things:

1. It stamps the datetimes the period returns
=============================================

:meth:`~isoperiod.Period.datetime` attaches the period's tzinfo to every datetime it produces, so interval
boundaries come back aware:

.. literalinclude:: ../examples/timezones.py
   :language: python
   :start-after: [start:stamping_returned_datetimes]
   :end-before: [end:stamping_returned_datetimes]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import timezones

   timezones.stamping_returned_datetimes()

2. It labels the clock, and is not applied to inputs
====================================================

All of a period's arithmetic runs on wall-clock fields. Any tzinfo on a datetime passed *in* is ignored - no
conversion happens, so the same wall-clock time always lands in the same interval:

.. literalinclude:: ../examples/timezones.py
   :language: python
   :start-after: [start:input_tzinfo_is_ignored]
   :end-before: [end:input_tzinfo_is_ignored]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import timezones

   timezones.input_tzinfo_is_ignored()

This is deliberate: an interval boundary at 09:00 stays at 09:00 on the clock the data was recorded against. It
also means **it is your responsibility to convert datetimes to the period's timezone before passing them in**, if
they might be on another clock.

3. It makes periods on different clocks distinct
================================================

A period at UTC is not equal to a naive one:

.. literalinclude:: ../examples/timezones.py
   :language: python
   :start-after: [start:periods_on_different_clocks_are_distinct]
   :end-before: [end:periods_on_different_clocks_are_distinct]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import timezones

   timezones.periods_on_different_clocks_are_distinct()

That is what stops two series recorded on different clocks being silently treated as compatible.

.. note::

   Sorting periods with mismatched tzinfo values raises :class:`TypeError`, just as sorting naive against aware
   datetimes does. Equality and hashing are safe in every case.

Showing the timezone
====================

:func:`repr` shows the timezone in square brackets - a named zone by its name, a fixed offset in ISO 8601 form,
and nothing at all when the period is naive:

.. literalinclude:: ../examples/timezones.py
   :language: python
   :start-after: [start:showing_the_timezone]
   :end-before: [end:showing_the_timezone]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import timezones

   timezones.showing_the_timezone()

Daylight saving
===============

.. warning::

   Because a period counts wall-clock time, a zone with daylight saving does **not** behave the way a fixed offset
   does. On a spring-forward day the local clock has 23 hours, but a period counting local time still sees 24
   one-hour intervals - one of which never occurred - and on an autumn day one interval covers two real hours.

The reliable approach for data spanning a daylight saying time transition is to do period arithmetic in UTC or in a
fixed offset, and convert to local time only for display:

.. literalinclude:: ../examples/timezones.py
   :language: python
   :start-after: [start:convert_before_asking]
   :end-before: [end:convert_before_asking]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import timezones

   timezones.convert_before_asking()

If your data is recorded on local standard time with no DST (as environmental monitoring data often is), a fixed
:class:`~datetime.timezone` offset is the right label and none of this applies.
