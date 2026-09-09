.. _documentation:

===================
Documentation guide
===================

Structure
=========

Our documentation is organized as follows:

.. code-block:: text

    docs/
    ├── source/
    │   ├── _static/           # Static assets (CSS, images)
    │   ├── developer/         # Developer guides (like this one)
    │   ├── getting_started/   # Installation and basic usage
    │   ├── user_guide/        # In-depth guides for features
    │   ├── examples/          # Runnable code the guide pages include
    │   ├── conf.py            # Sphinx configuration
    │   └── index.rst          # Main index page
    └── Makefile              # Build commands for Unix

Building Documentation
======================

To build the documentation:

.. code-block:: bash

    cd docs
    make html

View the result by opening ``docs/_build/html/index.html`` in a browser.

Review the build output for warnings and errors.

Creating a New Page
===================

To add a new page to the documentation:

1. Create a new ``.rst`` file in the appropriate directory.
2. Start with a title and introduction, then add any relevant sections for your documentation.
3. Add the page to the relevant **toctree** in ``index.rst``.

Code Examples
=============

User guide examples
-------------------

The Python for every guide page lives in ``docs/source/examples/``, one module per page. Each example is a
function whose body is wrapped in region markers:

.. code-block:: python

    def flooring() -> None:
        """Snap a timestamp down onto the grid of several periods."""
        # [start:flooring]
        d = datetime(2024, 3, 15, 9, 47, 30)

        print(Period.of_minutes(15).floor(d))
        # [end:flooring]

The page shows that region with ``literalinclude`` and renders its output with ``jupyter-execute``:

.. code-block:: rst

    .. literalinclude:: ../examples/intervals.py
       :language: python
       :start-after: [start:flooring]
       :end-before: [end:flooring]
       :dedent:

    .. jupyter-execute::
       :hide-code:

       intervals.flooring()

Because the markers sit inside the function, the code shown is the code that ran, and the output beneath it is
generated at build time rather than typed out. Setup that is not the point of the example goes *above* the
``# [start:...]`` marker, so it runs but is not shown.

Docstring examples
------------------

Docstrings use standard ``>>>`` doctests, with the expected output written beneath the call:

.. code-block:: python

    Examples:
        >>> from datetime import datetime
        >>> Period.of_minutes(15).floor(datetime(2024, 3, 15, 9, 47, 30))
        datetime.datetime(2024, 3, 15, 9, 45)

These are collected by pytest's ``--doctest-modules``, so a changed return value fails the suite. The module's
own globals are in scope, but import what a reader would need anyway.

Running the checks
------------------

Both run with the rest of the suite:

.. code-block:: bash

    pytest

To run just the docstring examples, or just the guide examples:

.. code-block:: bash

    pytest src/isoperiod/periods.py
    pytest tests/isoperiod/test_examples.py

A broken example also fails the documentation build, since ``jupyter-execute`` runs it:

.. code-block:: bash

    make -C docs html
