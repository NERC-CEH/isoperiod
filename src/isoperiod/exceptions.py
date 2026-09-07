from isoperiod.enums import Step


class PeriodError(Exception):
    """Base exception for all period-related errors."""


class PeriodConfigError(PeriodError):
    """Raised when constructing or configuring objects within the Period module with unsupported options."""


class PeriodParsingError(PeriodError):
    """Raised when things like a period string or timedelta cannot be parsed."""


class PeriodValidationError(PeriodError):
    """Raised when a validation on objects in the Period module fails."""


def illegal_step(step: int) -> PeriodValidationError:
    """Build the error raised when a Step value is not one of the three legal steps.

    Args:
        step: The offending step value

    Returns:
        A PeriodValidationError, for the caller to raise
    """
    return PeriodValidationError(f"Illegal step: '{step}'. Must be one of: {list(Step)}")
