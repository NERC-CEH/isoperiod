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

Examples are written inline, as ordinary ``code-block:: python`` directives, and are **executed as part of the
test suite**. `Sybil <https://sybil.readthedocs.io/>`_, configured in ``conftest.py``, collects every Python
example and runs it as a test:

- the reST pages under ``docs/source``
- the docstrings in ``src/isoperiod``, which are rendered into the API reference
- the fenced ``python`` blocks in ``README.md``

An example that raises, or whose ``assert`` no longer holds, fails the build. This is what stops the
documentation drifting away from the code.

Three conventions follow from that.

**State the expected result with an** ``assert``.
    An assertion is both the clearest way to show a reader what a call returns, and the thing that catches a
    changed value later. Prefer it to a comment.

**Examples in a documentation page share a namespace, in order.**
    Each document's examples run in sequence in one namespace, so an example may use names bound by an earlier one.
    Nothing carries over between documents, so the first example on a page must import what it needs.

**Docstring examples must stand alone.**
    A docstring example should import everything it uses, exactly as a reader would have to.

Excluding an example
--------------------

Occasionally an example cannot run - it needs an optional dependency, or is deliberately illustrative. Put a
``.. skip: next`` comment on the line above the ``code-block`` directive, and Sybil will leave it alone. The
comment renders as nothing, so the page is unchanged.

Use sparingly: an example should be tested unless absolutely necessary.

Running the check
-----------------

The examples run with the rest of the suite:

.. code-block:: bash

    pytest

To run only the examples from one page:

.. code-block:: bash

    pytest docs/source/user_guide/offsets.rst
