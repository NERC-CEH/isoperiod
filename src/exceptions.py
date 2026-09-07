class PeriodError(Exception):
    """Base exception for all period-related errors."""


class PeriodConfigError(PeriodError):
    """Raised when constructing or configuring objects within the Period module with unsupported options."""


class PeriodParsingError(PeriodError):
    """Raised when things like a period string or timedelta cannot be parsed."""


class PeriodValidationError(PeriodError):
    """Raised when a validation on objects in the Period module fails."""
