# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from importlib.metadata import version as get_version
from pathlib import Path

# Put this directory on the path so the user guide can import the "examples" package alongside it. PYTHONPATH is
# set as well as sys.path because jupyter-sphinx runs each "jupyter-execute" block in a separate kernel process,
# which does not inherit this one's sys.path.
_SOURCE_DIR = str(Path(__file__).parent)
sys.path.insert(0, _SOURCE_DIR)
os.environ["PYTHONPATH"] = os.pathsep.join(filter(None, [_SOURCE_DIR, os.environ.get("PYTHONPATH", "")]))

project = "isoperiod"
copyright = "2026, UKCEH"
author = "UKCEH"
release = get_version("isoperiod")
version = release

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_autodoc_typehints",
    "sphinx_contributors",
    "sphinx_iconify",
    # Runs the user guide's example code at build time and renders its output.
    "jupyter_sphinx",
    # Optional: uncomment as needed
    # "sphinx_tabs.tabs",
    # "sphinxcontrib.mermaid",
    # "matplotlib.sphinxext.plot_directive",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]

# -- jupyter-sphinx ----------------------------------------------------------
# Kernels talk to the build over ZeroMQ. ipykernel warns on every start that a TCP transport is unencrypted, so
# use Unix domain sockets instead: no ports are opened, and the warning goes away. Windows has no "ipc"
# transport, so it keeps the default. Everything else here is jupyter-sphinx's own default, which must be
# repeated because setting this replaces the value rather than adding to it.
jupyter_execute_kwargs = {"timeout": -1, "allow_errors": True, "store_widget_state": True}

if sys.platform != "win32":
    from traitlets.config import Config

    jupyter_execute_kwargs["config"] = Config({"KernelManager": {"transport": "ipc"}})

# -- Autodoc / autosummary ---------------------------------------------------
autosummary_generate = True
autodoc_typehints = "description"
autoclass_content = "class"
# Period is abstract and built through its factory methods, so keep the internal
# constructor signature off the class heading in the API reference.
autodoc_class_signature = "separated"

# -- HTML output -------------------------------------------------------------
html_theme = "shibuya"
html_static_path = ["_static"]
html_css_files = ["css/custom.css"]

html_context = {
    "license": "MIT",
}

html_theme_options = {
    "accent_color": "blue",
    "nav_links": [
        {"title": "Getting started", "url": "getting_started/installation"},
        {"title": "User guide", "url": "user_guide/creating"},
        {"title": "Development", "url": "developer/contributing"},
        {"title": "API reference", "url": "api/period"},
    ],
    "github_url": "https://github.com/NERC-CEH/isoperiod",
}

# Resolve references to stdlib types (datetime, timedelta, tzinfo ...) against the
# Python docs, so both :class:`...` roles and autodoc'd type hints become links.
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

# Single backticks in docstrings mean "literal code", not reST's default
# "title reference" (which renders as an italic <cite>).
default_role = "code"

# -- Napoleon settings -------------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_param = True
napoleon_use_rtype = False
