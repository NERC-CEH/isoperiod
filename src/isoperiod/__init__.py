"""Top-level package for isoperiod."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("isoperiod")
except PackageNotFoundError:
    __version__ = "unknown"
