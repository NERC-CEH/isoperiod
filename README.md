[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Language](https://img.shields.io/github/languages/top/NERC-CEH/isoperiod)
[![tests badge](https://github.com/NERC-CEH/isoperiod/actions/workflows/pipeline.yml/badge.svg)](https://github.com/NERC-CEH/isoperiod/actions)
[![Docs](https://img.shields.io/badge/docs-%F0%9F%93%9A%20online-blue)](https://nerc-ceh.github.io/isoperiod)


# isoperiod

ISO 8601 period and duration arithmetic, including offsets from the natural boundary, for defining sampling resolution
and periodicity in timeseries data

## Features

* **ISO 8601 durations** - build a period from `"PT15M"`, `"P1D"` or `"P1Y"`.
* **Offsets** - shift every interval boundary off its natural position, for hydrological days (`"P1D+T9H"`) and
  water years (`"P1Y+9MT9H"`).
* **Origins** - pin the grid to a chosen datetime with the `"2024-01-01/P7D"` form.
* **Ordinals** - every interval on the timeline has an integer ordinal, so flooring, stepping and grouping are
  integer arithmetic, calendar months included.
* **Alignment** - check that a timestamp sits on a period boundary, and whether one period nests cleanly inside
  another.
* **No runtime dependencies** - pure Python on top of `datetime`, with helpers for handing periods to Polars.

See the [documentation](https://nerc-ceh.github.io/isoperiod/) for a quick start, the concepts behind the API, and the full reference.

## License

This project is licensed under the [MIT license](LICENSE).

## Contributing

Contributions are welcome. Please feel free to submit a Pull Request.

1. Clone the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please make sure your code passes all tests and follows the coding style before submitting a PR.
See **developer setup** below for more information.

## Developer Setup

This is for active development on the isoperiod package itself.

### Requirements

#### Install uv

[Official instructions](https://docs.astral.sh/uv/getting-started/installation/)

### Clone the repository

```bash
git clone https://github.com/NERC-CEH/isoperiod.git
cd isoperiod
```

### Setting up and activating a virtual environment

```commandline
uv sync
source .venv/bin/activate
```

### Linting
Linting uses ruff using the config in pyproject.toml
```
ruff check --fix
```

### Formatting
Formating uses ruff using the config in pyproject.toml which follows the default black settings.
```
ruff format .
```

### Testing
Testing is done using pytest and tests are in the /tests directory.
```
pytest
```

### Pre commit hooks
Run below to setup the pre-commit hooks.
```
git config --local core.hooksPath .githooks/
```
This will set this repo up to use the git hooks in the `.githooks/` directory.
The hook runs `ruff format --check` and `ruff check` to prevent commits that are not formatted correctly or have errors.
The hook intentionally does not alter the files, but informs the user which command to run.

## Documentation

For full documentation, visit https://nerc-ceh.github.io/isoperiod/

To build the documentation locally:

```bash
# Install documentation dependencies (but they are included by default)
uv sync --group docs

# Build the documentation
cd docs
make html

# View documentation
open _build/html/index.html
```

## Citation

If you use this software, please cite it using the metadata in [`CITATION.cff`](./CITATION.cff).

Built with [Cookiecutter](https://github.com/cookiecutter/cookiecutter) and the [NERC-CEH/fdri-cookiecutter-templates](https://github.com/NERC-CEH/fdri-cookiecutter-templates) template.
