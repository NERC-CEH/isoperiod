import datetime as dt
import re
from dataclasses import dataclass

from isoperiod.enums import Step
from isoperiod.exceptions import PeriodValidationError
from isoperiod.iso import period_regex
from isoperiod.properties import Properties

# Regular expressions used to detect a truncated ("reduced precision") ISO 8601 date - i.e. a bare year or year-month
_RE_TRUNCATED_YEAR = re.compile(r"\d{4}")
_RE_TRUNCATED_YEAR_MONTH = re.compile(r"\d{4}-\d{2}")

# A regular expression Pattern used to parse an ISO 8601 duration, such as P1Y, P7M, P5Y3M, P8D9H1M4S, etc.
_RE_PERIOD = re.compile(r"^" r"[Pp]" + period_regex("period") + r"$")

# A regular expression Pattern used to parse our custom extended ISO 8601 duration string, such as P2Y+3M, P1Y+9M9H.
# This accounts for offsets on the period.
_RE_PERIOD_OFFSET = re.compile(r"^" r"[Pp]" + period_regex("period") + r"\+" + period_regex("offset") + r"$")


def str_to_int(num: str | None, default: int = 0) -> int:
    """Convert string to int, None becomes 0 (or default if specified)

    Args:
        num: The string to be converted, or None
        default: Default int value to use if num is None (defaults to 0)

    Returns:
        The int value read from the input string
    """
    return default if num is None else int(num)


def str_to_microseconds(num: str | None, default: int = 0) -> int:
    """Convert string to microseconds, None becomes 0 (or default if specified)

    A seconds + microseconds string looks like "nn.uuu". This function  converts the "uuu" part (from 1 to 6 digits)
    to an int value between 0 and 999_999.

    Args:
        num: The string to be converted, or None
        default: Default int value to use if num is None (defaults to 0)

    Returns:
        The int value read from the input string
    """
    return default if num is None else int((num + "00000")[:6])


@dataclass(frozen=True)
class MonthsSeconds:
    """A basic specification for either a period or a period offset where the period/offset amount is a number of
    months and/or seconds.
    """

    string: str
    months: int
    seconds: int
    microseconds: int

    def __post_init__(self) -> None:
        if (self.months < 0) or (self.seconds < 0) or (self.microseconds < 0) or (self.microseconds > 999_999):
            raise PeriodValidationError(f"Illegal period: {self.string}")
        if (self.months == 0) and (self.seconds == 0) and (self.microseconds == 0):
            raise PeriodValidationError(f"Illegal period: {self.string}")

    def get_step_and_multiplier(self) -> tuple[int, int]:
        """Return a tuple of two integers containing the
        calculated step and multiplier

        Returns:
            A tuple of (step,multiplier)

        Raises:
            ValueError if a valid step and multiplier
            cannot be created.  This happens, for example,
            if boths months and seconds are >0.
        """
        if (self.months > 0) and (self.seconds == 0) and (self.microseconds == 0):
            return Step.MONTHS, self.months
        if (self.months == 0) and (self.seconds > 0) and (self.microseconds == 0):
            return Step.SECONDS, self.seconds
        if (self.months == 0) and (self.microseconds > 0):
            return Step.MICROSECONDS, self.total_microseconds()
        raise PeriodValidationError(f"Illegal period: {self.string}")

    def total_microseconds(self) -> int:
        """Return total microseconds from the seconds
        and microseconds fields

        Returns:
            The total number of microseconds
        """
        return self.seconds * 1_000_000 + self.microseconds

    def get_base_properties(self) -> Properties:
        """Return a basic Properties object from the months
        and (seconds,microseconds) fields

        Raise an error if it is not possible to create
        a valid Properties object.  This happens if,
        for example, both months and seconds are >0.

        Returns:
            A Properties object
        """
        step, multiplier = self.get_step_and_multiplier()
        return Properties(
            step=step, multiplier=multiplier, month_offset=0, microsecond_offset=0, tzinfo=None, ordinal_shift=0
        )


@dataclass(frozen=True)
class PeriodFields:
    """A set of fields that can be read from an ISO 8601 format duration string."""

    string: str
    years: int
    months: int
    days: int
    hours: int
    minutes: int
    seconds: int
    microseconds: int

    def __post_init__(self) -> None:
        if (
            (self.years < 0)
            or (self.months < 0)
            or (self.days < 0)
            or (self.hours < 0)
            or (self.minutes < 0)
            or (self.seconds < 0)
            or (self.microseconds < 0)
            or (self.microseconds > 999_999)
        ):
            raise PeriodValidationError(f"Illegal period: {self.string}")

    def get_months_seconds(self) -> MonthsSeconds:
        """Return a MonthsSeconds object from the fields of an ISO 8601 duration

        Returns:
            A MonthsSeconds object
        """
        months = self.years * 12 + self.months
        seconds = (self.days * 86_400) + (self.hours * 3_600) + (self.minutes * 60) + self.seconds
        return MonthsSeconds(string=self.string, months=months, seconds=seconds, microseconds=self.microseconds)

    def get_base_properties(self) -> Properties:
        """Return a basic Properties object from the fields of an ISO 8601 duration

        Returns:
            A Properties object
        """
        return self.get_months_seconds().get_base_properties()


def _period_match(prefix: str, matcher: re.Match[str]) -> PeriodFields:
    """Return a PeriodFields object from a regex Matcher object

    The regex Pattern that create the matcher is assumed to have been created from a string returned by the
    period_regex function.

    Args:
        prefix: The name prefix used when creating the regex
        matcher: The regex Matcher object

    Returns:
        The PeriodFields object
    """
    return PeriodFields(
        string=matcher.string,
        years=str_to_int(matcher.group(f"{prefix}_years")),
        months=str_to_int(matcher.group(f"{prefix}_months")),
        days=str_to_int(matcher.group(f"{prefix}_days")),
        hours=str_to_int(matcher.group(f"{prefix}_hours")),
        minutes=str_to_int(matcher.group(f"{prefix}_minutes")),
        seconds=str_to_int(matcher.group(f"{prefix}_seconds")),
        microseconds=str_to_microseconds(matcher.group(f"{prefix}_microseconds")),
    )


def _pad_truncated_date(text: str) -> str:
    """Pad a truncated ISO 8601 date ("yyyy" or "yyyy-mm") out to a full "yyyy-mm-dd", defaulting the missing month
    and/or day to "01" - matching ISO 8601's convention that a reduced-precision date/time represents its first instant.

    Args:
        text: The (possibly truncated) date/datetime string

    Returns:
        `text` unchanged if it wasn't truncated, otherwise the padded string
    """
    if _RE_TRUNCATED_YEAR.fullmatch(text):
        return f"{text}-01-01"
    if _RE_TRUNCATED_YEAR_MONTH.fullmatch(text):
        return f"{text}-01"
    return text


def _parse_start_datetime(text: str) -> dt.datetime | None:
    """Parse the "<start>" half of a "<start>/<duration>" string into a datetime, or return None if it isn't a valid
    (possibly truncated) ISO 8601 date/datetime.

    Args:
        text: The "<start>" string

    Returns:
        A datetime object, or None
    """
    try:
        return dt.datetime.fromisoformat(_pad_truncated_date(text))
    except ValueError:
        return None


def parse_iso_duration(iso_8601_duration: str) -> Properties | None:
    """Parse a plain ISO 8601 duration string (e.g. "P1Y" or "PT15M") into a Properties object, or return None if the
    string doesn't match this format.
    """
    matcher = _RE_PERIOD.match(iso_8601_duration)
    if matcher is None:
        return None
    return _period_match("period", matcher).get_base_properties()


def parse_period_offset(duration: str) -> Properties | None:
    """Parse the extended "<duration>+<offset>" form (e.g. "P1D+T9H") into a Properties object, or return None if
    the string doesn't match this format.
    """
    matcher = _RE_PERIOD_OFFSET.match(duration)
    if matcher is None:
        return None
    period_fields = _period_match("period", matcher)
    offset_fields = _period_match("offset", matcher)
    return period_fields.get_base_properties().with_offset_period_fields(offset_fields)


def parse_date_and_duration(date_duration: str) -> tuple[Properties, dt.datetime] | None:
    """Parse a "<start>/<duration>" string (e.g. "1883-01-01/P1D") into a (Properties, origin datetime) pair, or
    return None if the string doesn't match this format.

    The caller is responsible for applying the origin (via Period.with_origin) to the Period built from the Properties.
    """
    start_text, sep, duration_text = date_duration.partition("/")
    if not sep:
        return None
    origin = _parse_start_datetime(start_text)
    if origin is None:
        return None
    matcher = _RE_PERIOD.match(duration_text)
    if matcher is None:
        return None
    properties = _period_match("period", matcher).get_base_properties()
    return properties, origin
