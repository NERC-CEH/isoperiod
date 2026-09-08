"""Collect the Python examples in the documentation as tests, so the docs cannot go stale.

Sybil finds every ``.. code-block:: python`` in the reST pages under ``docs/source`` and in the docstrings of
``src/isoperiod`` (which are rendered into the API reference), plus the ``python`` blocks in the README, and runs each
one as a test.

An example that raises, or whose ``assert`` no longer holds, fails the build.

To exclude an example that cannot run - one needing an optional dependency, say - precede it with a ``.. skip: next``
comment, which renders as nothing - use sparingly.
"""

from sybil import Sybil
from sybil.parsers import markdown, rest

_rest_examples = Sybil(
    parsers=[rest.PythonCodeBlockParser(), rest.SkipParser()],
    patterns=["*.rst", "*.py"],
)

_markdown_examples = Sybil(
    parsers=[markdown.PythonCodeBlockParser(), markdown.SkipParser()],
    patterns=["*.md"],
)

pytest_collect_file = (_rest_examples + _markdown_examples).pytest()
