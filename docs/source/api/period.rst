.. _period_api:

======
Period
======

.. currentmodule:: isoperiod

.. autoclass:: Period
    :exclude-members: __init__

Constructors
============

.. rubric:: From a named unit

.. autosummary::
    :nosignatures:
    :toctree: _api/

    ~Period.of_years
    ~Period.of_months
    ~Period.of_days
    ~Period.of_hours
    ~Period.of_minutes
    ~Period.of_seconds
    ~Period.of_microseconds

.. rubric:: From a string or timedelta

.. autosummary::
    :nosignatures:
    :toctree: _api/

    ~Period.of
    ~Period.of_iso_duration
    ~Period.of_duration
    ~Period.of_date_and_duration
    ~Period.of_timedelta

Attributes
==========

.. autosummary::
    :nosignatures:
    :toctree: _api/

    ~Period.iso_duration
    ~Period.timedelta
    ~Period.tzinfo
    ~Period.offset
    ~Period.month_offset
    ~Period.microsecond_offset
    ~Period.min_ordinal
    ~Period.max_ordinal
    ~Period.pl_interval
    ~Period.pl_offset

Methods
=======

.. rubric:: Intervals and ordinals

.. autosummary::
    :nosignatures:
    :toctree: _api/

    ~Period.ordinal
    ~Period.datetime
    ~Period.is_aligned

.. rubric:: Builders

Every builder returns a new :class:`Period`; none mutate the original.

.. autosummary::
    :nosignatures:
    :toctree: _api/

    ~Period.with_year_offset
    ~Period.with_month_offset
    ~Period.with_day_offset
    ~Period.with_hour_offset
    ~Period.with_minute_offset
    ~Period.with_second_offset
    ~Period.with_microsecond_offset
    ~Period.with_origin
    ~Period.with_tzinfo
    ~Period.without_offset
    ~Period.without_ordinal_shift
    ~Period.base_period

.. rubric:: Comparison

.. autosummary::
    :nosignatures:
    :toctree: _api/

    ~Period.count
    ~Period.is_subperiod_of
    ~Period.has_offset
    ~Period.is_epoch_agnostic
