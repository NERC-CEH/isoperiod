.. _interoperability:

================
Interoperability
================

.. rst-class:: lead

    Describing a period as a string, and handing it to other tools.

.. code-block:: python

    from datetime import timedelta
    from isoperiod import Period

Describing a period as a string
===============================

Three representations, for three purposes:

.. list-table::
   :header-rows: 1
   :widths: 20 30 40

   * - Form
     - ``Period.of("P1D+T9H")``
     - Use for
   * - :attr:`~isoperiod.Period.iso_duration`
     - ``"P1D"``
     - strict ISO 8601 - the duration alone, no offset
   * - ``str()``
     - ``"P1D+T9H"``
     - round-tripping through :meth:`~isoperiod.Period.of`
   * - ``repr()``
     - ``"P1D+T9H[]"``
     - debugging - adds timezone and ordinal shift

.. code-block:: python

    water_day = Period.of("P1D+T9H")

    assert water_day.iso_duration == "P1D"
    assert str(water_day) == "P1D+T9H"
    assert repr(water_day) == "P1D+T9H[]"

    assert Period.of(str(water_day)) == water_day  # str round-trips

The ``repr()`` form appends the timezone in square brackets (empty when naive) and any ordinal shift, so a
period with an origin is distinguishable from one without:

.. code-block:: python

    assert repr(Period.of("2024-01-01/P7D")) == "P7D+1D[]-105555"

.. note::

   :attr:`~isoperiod.Period.iso_duration` deliberately drops the offset, so it is not enough to reconstruct an
   offset period. Persist ``str()`` if you need the period back.

Converting to a timedelta
=========================

A period whose step is seconds or microseconds has a fixed length, so it converts:

.. code-block:: python

    assert Period.of_minutes(15).timedelta == timedelta(minutes=15)
    assert Period.of_days(1).timedelta == timedelta(days=1)
    assert Period.of("PT0.04S").timedelta == timedelta(microseconds=40_000)

Months and years do not, and return ``None`` rather than an approximation:

.. code-block:: python

    assert Period.of_months(1).timedelta is None
    assert Period.of_years(1).timedelta is None

Always check for ``None`` before doing timedelta arithmetic - or better, use
:meth:`~isoperiod.Period.ordinal` and :meth:`~isoperiod.Period.datetime`, which work for calendar periods too.

Using periods with Polars
=========================

Two properties emit `Polars <https://docs.pola.rs/>`_ duration strings, so a period can drive a Polars grouping
or range directly:

.. code-block:: python

    assert Period.of_minutes(15).pl_interval == "900s"
    assert Period.of_months(1).pl_interval == "1mo"
    assert Period.of("PT0.04S").pl_interval == "40000us"

    assert Period.of("P1D+T9H").pl_offset == "0mo32400000000us"
    assert Period.of("P1Y+9M").pl_offset == "9mo0us"

:attr:`~isoperiod.Period.pl_interval` gives the period's length, for arguments such as ``every`` and
``interval``; :attr:`~isoperiod.Period.pl_offset` gives its offset, for ``offset`` and ``Expr.dt.offset_by``:

.. skip: next

.. code-block:: python

    import polars as pl                       # not a dependency of isoperiod

    water_day = Period.of("P1D+T9H")

    daily = df.group_by_dynamic(
        "timestamp",
        every=water_day.pl_interval,
        offset=water_day.pl_offset,
    ).agg(pl.col("flow").mean())
