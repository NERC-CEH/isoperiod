[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Language](https://img.shields.io/github/languages/top/NERC-CEH/isoperiod)
[![tests badge](https://github.com/NERC-CEH/isoperiod/actions/workflows/pipeline.yml/badge.svg)](https://github.com/NERC-CEH/isoperiod/actions)
[![Docs](https://img.shields.io/badge/docs-%F0%9F%93%9A%20online-blue)](https://nerc-ceh.github.io/isoperiod)


# isoperiod

ISO 8601 period and duration arithmetic, including offsets from the natural boundary, for defining sampling resolution
and periodicity in timeseries data

## Features

* TODO

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

## Installing isoperiod

Whilst isoperiod is under active development, to use isoperiod within your project you can do one of two things:

1. Clone the isoperiod repository to a location next to your project's repository. Then, you can install using a relative path.

    When you install a package in editable mode, any changes to the source code are immediately
    available to any projects using the package.

    **Using uv directly**
    ```commandline
    uv add --editable /path/to/isoperiod
    ```

    **In your project's pyproject.toml**
    ```toml
    [project]
    dependencies = [
        "isoperiod"
    ]
    [tool.uv.sources]
    isoperiod = { path = "/path/to/isoperiod", editable = true }
    ```

    Now when changes have been made to isoperiod, you can just do a `git pull` in your cloned directory to get the
    changes, and they will be automatically available in your package.

2. Use the isoperiod git url

    **Using uv directly**
    ```commandline
    uv add git+https://github.com/NERC-CEH/isoperiod.git
    ```

    **In your project's pyproject.toml**
    ```toml
    [project]
    dependencies = [
        "isoperiod"
    ]
    [tool.uv.sources]
    isoperiod = { git = "https://docs.astral.sh/uv/getting-started/installation/" }
    ```

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
