.. _concepts:

========
Concepts
========

.. rst-class:: lead

    Understand the concepts that **isoperiod** is built on.

There is one public class, :class:`~isoperiod.Period`, and it does one essential thing: cuts the timeline into
consecutive intervals and numbers them. Everything else in the package follows from that.

Intervals
=========

**What it is:** a period divides *all* of time into back-to-back intervals of one fixed size - every hour, every
15 minutes, every calendar month. There are no gaps and no overlaps, so every datetime falls in exactly one
interval.

.. code-block:: text

                      interval n-1     interval n     interval n+1
                    ├───────────────┼───────────────┼───────────────┤
    timeline ...  08:00           09:00           10:00           11:00 ...
                                                 ▲
                                               09:47

**Why it matters:** it means "which hour is this reading in?" and "when did that hour start?" are both answerable,
for any timestamp.

Ordinals
========

**What it is:** the integer that identifies one interval. Consecutive intervals get consecutive ordinals, so the
interval after ordinal ``n`` is always ``n + 1``.

Two methods map between the two views of the timeline:

- :meth:`~isoperiod.Period.ordinal` takes a datetime and returns the ordinal of the interval containing it.
- :meth:`~isoperiod.Period.datetime` takes an ordinal and returns the **first instant** of that interval.

**Why it matters:**

- **Interval arithmetic becomes integer arithmetic.** "The interval three steps back" is ``n - 3``, whether a step
  is 15 minutes or a calendar month.
- **Grouping is free.** Two timestamps belong to the same interval exactly when their ordinals are equal, so an
  ordinal is a ready-made grouping key.
- **Truncation is exact.** :meth:`~isoperiod.Period.floor` snaps ``d`` to its interval boundary, including for months
  and years, which a ``timedelta`` can't do.

.. note::

   An ordinal only means something to the period that produced it. Each period numbers the timeline in its own
   units, so feeding one period's ordinal to another period's :meth:`~isoperiod.Period.datetime` gives a wrong
   answer rather than an error.

Step and multiplier
===================

**What it is:** every period is a whole number of one of three fundamental units:

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Step
     - Used for
     - Example
   * - months
     - months, quarters, years
     - ``P1Y`` is 12 months; ``P3M`` is 3 months
   * - seconds
     - seconds, minutes, hours, days
     - ``PT15M`` is 900 seconds; ``P1D`` is 86,400 seconds
   * - microseconds
     - sub-second sampling
     - ``PT0.04S`` (25 Hz) is 40,000 microseconds

**Why it matters:** months and years are the odd ones out - they have no fixed length in seconds, so they are
counted on their own timeline rather than converted. That is why
:attr:`Period.timedelta <isoperiod.Period.timedelta>` is ``None`` for a monthly period, and why a monthly period
never divides evenly into a daily one.

It also means periods that describe the same grid are the same object: ``P1Y`` and ``P12M`` are equal, as are
``PT1M`` and ``PT60S``.

Natural boundaries
==================

**What it is:** by default a period's intervals fall on the natural boundaries of their unit - the obvious
"start line" from which the interval repeats:

- a **year** starts at 00:00 on 1 January
- a **month** starts at 00:00 on the 1st
- a **day** starts at midnight
- an **hour** starts on the hour, a **15-minute** interval at :00, :15, :30 and :45

**Why it matters:** it is what makes a ``Period.of("P1D")`` mean the thing everybody expects - a
calendar day - without having to choose an origin.

Offsets
=======

**What it is:** an offset moves *every* interval boundary by a fixed amount. The intervals keep their size; only
their phase changes.

.. code-block:: text

    P1D        ├──────────────┼──────────────┼──────────────┤
               14 Mar         15 Mar         16 Mar         17 Mar
               00:00          00:00          00:00          00:00

    P1D+T9H          ├──────────────┼──────────────┼──────────────┤
                     14 Mar         15 Mar         16 Mar         17 Mar
                     09:00          09:00          09:00          09:00

**Examples:**

- ``P1D+T9H`` - a **hydrological day**, running 09:00 to 09:00
- ``P1Y+9MT9H`` - a **water year**, starting 09:00 on the 1 October
- ``PT15M+T5M`` - a sensor reporting at :05, :20, :35 and :50

**Why it matters:** real measurement regimes may not sit on the natural boundary. Encoding the offset in the period
means the rest of your code does not need to know about it - alignment checks, truncation and nesting all account
for it automatically.

Origin
======

**What it is:** the datetime that gets ordinal ``0``. Setting an origin does two things at once: it pins the
numbering, and it aligns the interval boundaries so that the origin *is* a boundary.

.. literalinclude:: ../examples/concepts.py
   :language: python
   :start-after: [start:origins]
   :end-before: [end:origins]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import concepts

   concepts.origins()

**Why it matters:** for periods that have no meaningful natural boundary - a 7-day period, a 10-minute period on
an instrument started at an arbitrary time - the origin is what fixes the grid. An offset changes *where the
boundaries are*; an origin changes the boundaries **and** the numbering.

Alignment
=========

**What it is:** a datetime is *aligned* to a period when it lands exactly on one of that period's interval
boundaries.

.. literalinclude:: ../examples/concepts.py
   :language: python
   :start-after: [start:alignment]
   :end-before: [end:alignment]
   :dedent:

**Why it matters:** it is the validation step for incoming data. A series claiming to be hourly should have every
timestamp on the hour; a hydrological day series should sit on 09:00. Because the check runs against the period
itself, offsets are handled without extra code.

Time zones
==========

**What it is:** a period can carry a :class:`~datetime.tzinfo`, but it is a **label**, not a conversion. All of a
period's arithmetic works on wall-clock fields; the tzinfo says which clock those fields belong to, is stamped onto
every datetime the period returns, and makes the period distinct from an otherwise identical one on another clock.

**Why it matters:** interval boundaries stay where you expect them (09:00 local is 09:00, whatever the UTC offset),
and two series recorded on different clocks are never silently treated as compatible. See
:doc:`/user_guide/timezones` for the details, including what this means around daylight saving.

Epoch-agnostic periods
======================

**What it is:** some periods split the timeline the same way no matter where the counting starts, and some do not.
``P1D``, ``PT15M`` and ``P1M`` are *epoch agnostic* - their length divides evenly into the fixed unit above them
(a day, a year). ``P7D`` is not: which seven days form an interval depends entirely on where you begin counting.

.. literalinclude:: ../examples/concepts.py
   :language: python
   :start-after: [start:epoch_agnosticism]
   :end-before: [end:epoch_agnosticism]
   :dedent:

**Why it matters:** an epoch-agnostic period is safe to exchange between systems on its own - everyone agrees on
where its boundaries fall. One that is not needs an explicit origin alongside it to be unambiguous, so exchange it
as ``"2024-01-01/P7D"`` rather than ``"P7D"``.

.. note::

   Adding an origin does not make a period epoch agnostic - the check looks only at the period's length, so
   ``Period.of("2024-01-01/P7D").is_epoch_agnostic()`` is still ``False``. The two answer different questions:
   :meth:`~isoperiod.Period.is_epoch_agnostic` asks whether the length alone determines the boundaries, while an
   origin is how you pin the boundaries of a length that does not.

Next steps
==========

- :doc:`quick-start` - the same ideas, as working code.
- :doc:`/user_guide/creating` - every way to build a period.
