.. _exceptions_api:

==========
Exceptions
==========

.. currentmodule:: isoperiod

Every error raised by isoperiod derives from :class:`PeriodError`, so catching that one handles them all.

.. code-block:: text

    PeriodError
    ├── PeriodParsingError      the string does not match any supported format
    └── PeriodValidationError   parsed, but does not describe a usable period

.. autoexception:: PeriodError
    :show-inheritance:

.. autoexception:: PeriodParsingError
    :show-inheritance:

.. autoexception:: PeriodValidationError
    :show-inheritance:

See :ref:`creating_periods` for how these come up in practice.
