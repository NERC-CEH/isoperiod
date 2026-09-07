from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("isoperiod")
except PackageNotFoundError:
    __version__ = "unknown"


from isoperiod.exceptions import PeriodError, PeriodParsingError, PeriodValidationError
from isoperiod.periods import Period

__all__ = [
    "Period",
    "PeriodError",
    "PeriodParsingError",
    "PeriodValidationError",
]
