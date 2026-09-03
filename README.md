# isoperiod

ISO 8601 period and duration arithmetic, including offsets from the natural boundary, for defining sampling resolution and periodicity in timeseries data

* [GitHub](https://github.com/richjam/isoperiod/) | [Documentation](https://richjam.github.io/isoperiod/)

## Features

* TODO

## Documentation

Documentation is built with [Sphinx](https://www.sphinx-doc.org/) and deployed to GitHub Pages.

* **Live site:** https://richjam.github.io/isoperiod/
* **Preview locally:** `make docs-serve` (serves at http://localhost:8000)
* **Build:** `make docs-build`

API documentation is auto-generated from docstrings using [sphinx-autodoc](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html).

## Development

To set up for local development:

```bash
git clone git@github.com:richjam/isoperiod.git
cd isoperiod
uv sync
```

Run tests:

```bash
uv run pytest
```

Run quality checks (format, lint, type check, test):

```bash
make qa
```

## Citation

If you use this software, please cite it using the metadata in [`CITATION.cff`](./CITATION.cff).

## Licence

MIT

Built with [Cookiecutter](https://github.com/cookiecutter/cookiecutter) and the [NERC-CEH/fdri-cookiecutter-templates](https://github.com/NERC-CEH/fdri-cookiecutter-templates) template.
