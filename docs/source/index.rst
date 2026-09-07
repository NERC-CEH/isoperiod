.. _index:

:layout: landing

=========
isoperiod
=========

.. rst-class:: lead

    A small, dependency-free Python library for working with **ISO 8601 periods**: the repeating intervals that give
    timeseries data its sampling resolution and periodicity.

    Includes customised ISO 8601 intervals which can have an offset from their natural boundary, such as a hydrological
    day running 09:00 to 09:00.

Current version: |release|

.. container:: buttons

    `Docs <getting_started/installation.html>`_
    `GitHub <https://github.com/NERC-CEH/isoperiod>`_

.. grid:: 1 1 2 3
    :gutter: 2
    :padding: 0
    :class-row: surface

    .. grid-item-card:: :octicon:`clock` ISO 8601 durations

        Build a period from ISO 8601 string formats: e.g. ``"PT15M"``, ``"P1D"``, ``"P1Y"``

    .. grid-item-card:: :octicon:`arrow-right` Offsets

        Shift every interval boundary off its natural position: e.g. a day that starts at 09:00, or a year that starts
        in October.

    .. grid-item-card:: :octicon:`number` Ordinals

        Every interval on the timeline has an integer ordinal, so *interval* arithmetic is just *integer* arithmetic.

    .. grid-item-card:: :octicon:`check-circle` Alignment

        Ask whether a timestamp sits on a period boundary, and whether one period nests cleanly inside another.

    .. grid-item-card:: :octicon:`typography` Formatting

        Render a timestamp to exactly the precision its period justifies.

    .. grid-item-card:: :octicon:`package` No dependencies

        Pure Python on top of :mod:`datetime`, with helpers for handing periods to Polars.

Why isoperiod?
==============

Timeseries data is generally measured on a structured grid: every 15 minutes, every day, every water year.
**isoperiod** makes that grid a first-class object to help enforce rules and properties that can help keep your
timeseries code in check.

- **Core Period object.** A :class:`~isoperiod.Period` splits the whole timeline into consecutive, numbered
  intervals, and maps freely between a datetime and the interval that contains it.
- **Offsets built in.** Hydrological days, water years, sensors reporting at five past the quarter hour - all
  expressible and comparable with each other.
- **Domain knowledge.** Built by software engineers and data scientists at `UKCEH <https://www.ceh.ac.uk/>`_
  from years of experience with hydrological and environmental data.
- **Small and dependency-free.** Standard library only, so it drops into any project.

isoperiod is the period engine behind `Time-Stream <https://nerc-ceh.github.io/time-stream/>`_, and is published
separately so it can be used on its own.

.. container:: image-row

   .. container:: image-item

      .. figure:: _static/UKCEH_Logo_Master_Black.png
         :alt: UKCEH
         :height: 100px
         :target: https://www.ceh.ac.uk

   .. container:: image-item

      .. figure:: _static/fdri_logo.png
         :alt: FDRI
         :height: 100px
         :target: https://fdri.org.uk

Community
=========

Developed at `UKCEH <https://www.ceh.ac.uk/>`_, welcoming community engagement and contributions.

License
=======

This project is licensed under the `MIT <https://github.com/NERC-CEH/isoperiod/blob/main/LICENSE>`_.


.. toctree::
    :hidden:
    :maxdepth: 2
    :caption: Getting started

    getting_started/installation
    getting_started/quick-start
    getting_started/concepts

.. toctree::
    :hidden:
    :maxdepth: 1
    :caption: User guide

    user_guide/creating
    user_guide/intervals
    user_guide/offsets
    user_guide/comparing
    user_guide/timezones
    user_guide/interop

.. toctree::
    :hidden:
    :maxdepth: 1
    :caption: API reference

    api/period
    api/exceptions

.. toctree::
    :hidden:
    :maxdepth: 2
    :caption: Developer guide

    developer/contributing
    developer/documentation
