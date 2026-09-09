.. _describing_a_period:

===================
Describing a period
===================

.. rst-class:: lead

    Rendering a period as English words for display.

Two properties turn a period into text for humans: :attr:`~isoperiod.Period.verbose` and
:attr:`~isoperiod.Period.descriptive`.

.. literalinclude:: ../examples/describing.py
   :language: python
   :start-after: [start:verbose_and_descriptive]
   :end-before: [end:verbose_and_descriptive]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import describing

   describing.verbose_and_descriptive()

:attr:`~isoperiod.Period.verbose`
    Spells the duration out in full, e.g. ``"1 year, 6 months"``.

:attr:`~isoperiod.Period.descriptive`
    Names the frequency with a common word where one exists, e.g. ``"Yearly"``, falling back to the plain
    ``verbose`` duration otherwise

.. note::

    Neither string form provided by these two properties is accepted by :meth:`~isoperiod.Period.of` or any
    other constructor - :attr:`~isoperiod.Period.iso_duration` and :meth:`str` remain the only parseable string forms.
    These are simply for display purposes.

Frequency words
===============

.. list-table::
   :header-rows: 1
   :widths: 15 30

   * - Period
     - Frequency word
   * - ``PT1H``
     - Hourly
   * - ``P1D``
     - Daily
   * - ``P7D``
     - Weekly
   * - ``P1M``
     - Monthly
   * - ``P3M``
     - Quarterly
   * - ``P1Y``
     - Yearly

There is no common word for a second or a minute on its own, so those fall back too, alongside everything else:

.. literalinclude:: ../examples/describing.py
   :language: python
   :start-after: [start:frequency_words]
   :end-before: [end:frequency_words]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import describing

   describing.frequency_words()

Named periods
=============

Two special periods are recognised by name, alongside their frequency word:

.. literalinclude:: ../examples/describing.py
   :language: python
   :start-after: [start:named_periods]
   :end-before: [end:named_periods]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import describing

   describing.named_periods()

Offsets and origins
====================

An offset appears in brackets. An origin replaces it rather than joining it:

.. literalinclude:: ../examples/describing.py
   :language: python
   :start-after: [start:offset_and_origin]
   :end-before: [end:offset_and_origin]
   :dedent:

.. jupyter-execute::
   :hide-code:

   from examples import describing

   describing.offset_and_origin()
