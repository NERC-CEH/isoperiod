.. _interoperability:

================
Interoperability
================

.. rst-class:: lead

    Describing a period as a string, and handing it to other tools.

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
     - ``"P1D+T9H"``
     - logging and debugging - as ``str()``, plus the timezone

.. literalinclude:: ../examples/interop.py
   :language: python
   :start-after: [start:string_forms]
   :end-before: [end:string_forms]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import interop

   interop.string_forms()

A period with an origin renders in the ``<origin>/<duration>`` form, so it round-trips too:

.. literalinclude:: ../examples/interop.py
   :language: python
   :start-after: [start:origin_round_trip]
   :end-before: [end:origin_round_trip]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import interop

   interop.origin_round_trip()

:func:`repr` differs from ``str()`` only by adding the timezone, which ``str()`` leaves out because
:meth:`~isoperiod.Period.of` cannot read one back:

.. literalinclude:: ../examples/interop.py
   :language: python
   :start-after: [start:repr_adds_the_timezone]
   :end-before: [end:repr_adds_the_timezone]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import interop

   interop.repr_adds_the_timezone()

Use ``repr()`` - or ``f"{period!r}"`` - in log lines and error messages, where the timezone matters and nothing
is going to parse the result back.

.. note::

   :attr:`~isoperiod.Period.iso_duration` deliberately drops the offset, so it is not enough to reconstruct an
   offset period. Persist ``str()`` if you need the period back.

Converting to a timedelta
=========================

A period whose step is seconds or microseconds has a fixed length, so it converts:

Months and years do not, and return ``None`` rather than an approximation:

.. literalinclude:: ../examples/interop.py
   :language: python
   :start-after: [start:to_timedelta]
   :end-before: [end:to_timedelta]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import interop

   interop.to_timedelta()

Always check for ``None`` before doing timedelta arithmetic - or better, use
:meth:`~isoperiod.Period.ordinal` and :meth:`~isoperiod.Period.datetime`, which work for calendar periods too.

Using periods with Polars
=========================

Two properties emit `Polars <https://docs.pola.rs/>`_ duration strings, so a period can drive a Polars grouping
or range directly:

.. literalinclude:: ../examples/interop.py
   :language: python
   :start-after: [start:polars_duration_strings]
   :end-before: [end:polars_duration_strings]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import interop

   interop.polars_duration_strings()

:attr:`~isoperiod.Period.pl_interval` gives the period's length, for arguments such as ``every`` and
``interval``; :attr:`~isoperiod.Period.pl_offset` gives its offset, for ``offset`` and ``Expr.dt.offset_by``:

.. literalinclude:: ../examples/interop.py
   :language: python
   :start-after: [start:polars_group_by_dynamic]
   :end-before: [end:polars_group_by_dynamic]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import interop

   interop.polars_group_by_dynamic()

Every window starts at 09:00, so the hourly readings are grouped into hydrological days rather than calendar ones.
The first and last are partial, because the data does not begin or end on a 09:00 boundary.
