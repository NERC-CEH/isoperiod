.. _timezones:

==========
Time zones
==========

.. rst-class:: lead

    A period's timezone is a label on the clock it counts, not a conversion.

A period can carry a :class:`~datetime.tzinfo`, set with :meth:`~isoperiod.Period.with_tzinfo`:

.. code-block:: python

    from datetime import datetime, timedelta, timezone
    from isoperiod import Period

    hourly_utc = Period.of_hours(1).with_tzinfo(timezone.utc)

    assert hourly_utc.tzinfo == timezone.utc

The tzinfo does three things:

1. It stamps the datetimes the period returns
=============================================

:meth:`~isoperiod.Period.datetime` attaches the period's tzinfo to every datetime it produces, so interval
boundaries come back aware:

.. code-block:: python

    n = hourly_utc.ordinal(datetime(2024, 3, 1, 9, 30))
    assert hourly_utc.datetime(n) == datetime(2024, 3, 1, 9, 0, tzinfo=timezone.utc)

2. It labels the clock, and is not applied to inputs
====================================================

All of a period's arithmetic runs on wall-clock fields. Any tzinfo on a datetime passed *in* is ignored - no
conversion happens, so the same wall-clock time always lands in the same interval:

.. code-block:: python

    ist = timezone(timedelta(hours=5, minutes=30))
    d = datetime(2024, 3, 1, 9, 30)

    assert hourly_utc.ordinal(d) == hourly_utc.ordinal(d.replace(tzinfo=timezone.utc))
    assert hourly_utc.ordinal(d) == hourly_utc.ordinal(d.replace(tzinfo=ist))

This is deliberate: an interval boundary at 09:00 stays at 09:00 on the clock the data was recorded against. It
also means **it is your responsibility to convert datetimes to the period's timezone before passing them in**, if
they might be on another clock.

3. It makes periods on different clocks distinct
================================================

A period at UTC is not equal to a naive one, nor to one at another offset, and neither nests inside the other:

.. code-block:: python

    assert Period.of_hours(1) != hourly_utc

That is what stops two series recorded on different clocks being silently treated as compatible.

.. note::

   Sorting periods with mismatched tzinfo values raises :class:`TypeError`, just as sorting naive against aware
   datetimes does. Equality and hashing are safe in every case.

Showing the timezone
====================

:func:`repr` shows the timezone in square brackets:

.. code-block:: python

    assert repr(Period.of_hours(1).with_tzinfo(timezone.utc)) == "PT1H[Z]"
    assert repr(Period.of_hours(1).with_tzinfo(ist)) == "PT1H[+05:30]"
    assert repr(Period.of_hours(1)) == "PT1H[]"

Daylight saving
===============

.. warning::

   Because a period counts wall-clock time, a zone with daylight saving does **not** behave the way a fixed offset
   does. On a spring-forward day the local clock has 23 hours, but a period counting local time still sees 24
   one-hour intervals - one of which never occurred - and on an autumn day one interval covers two real hours.

The reliable approach for data spanning a daylight saying time transition is to do period arithmetic in UTC or in a
fixed offset, and convert to local time only for display:

.. code-block:: python

    utc_daily = Period.of_days(1).with_tzinfo(timezone.utc)

    local_reading = datetime(2024, 3, 31, 2, 30, tzinfo=ist)
    utc_reading = local_reading.astimezone(timezone.utc)    # convert first ...
    n = utc_daily.ordinal(utc_reading)                      # ... then ask the period

    assert utc_daily.datetime(n) == datetime(2024, 3, 30, tzinfo=timezone.utc)

If your data is recorded on local standard time with no DST (as environmental monitoring data often is), a fixed
:class:`~datetime.timezone` offset is the right label and none of this applies.
