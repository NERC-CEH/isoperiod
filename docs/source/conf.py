# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from importlib.metadata import version as get_version

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
    # Optional: uncomment as needed
    # "sphinx_tabs.tabs",
    # "sphinxcontrib.mermaid",
    # "jupyter_sphinx",
    # "matplotlib.sphinxext.plot_directive",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]

# -- Autodoc / autosummary ---------------------------------------------------
autosummary_generate = True
autodoc_typehints = "description"
autoclass_content = "class"

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
        {"title": "Installation", "url": "installation"},
        {"title": "API reference", "url": "api"},
    ],
    "github_url": "https://github.com/richjam/isoperiod",
}

# -- Napoleon settings -------------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_param = True
napoleon_use_rtype = False
