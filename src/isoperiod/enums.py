from enum import IntEnum


class Step(IntEnum):
    """The fundamental units of a Period.

    A Period's duration is always some multiplier of one of these steps, e.g. a 15-minute period is 900 seconds,
    a 1-year period is 12 months.
    """

    MICROSECONDS = 1
    SECONDS = 2
    MONTHS = 3


class Precision(IntEnum):
    """How much of a datetime to keep when formatting it, from YEAR down to MICROSECOND.

    Examples (for ``datetime(2024, 3, 1, 9, 30)``):
        .. code-block:: text

            Precision.DAY    -> "2024-03-01"
            Precision.MINUTE -> "2024-03-01T09:30"
    """

    YEAR = 1
    MONTH = 2
    DAY = 3
    HOUR = 4
    MINUTE = 5
    SECOND = 6
    MILLISECOND = 7
    MICROSECOND = 8


class CountResult(IntEnum):
    """The two non-count values that Properties.count()/Period.count() can return.

    count() normally returns a positive number of intervals, but falls back to one of
    these when no such number exists. The numeric values are part of the documented
    public contract of Period.count(), and Period.is_subperiod_of() relies on
    UNALIGNED being the only negative one (it tests ``count(other) >= 0``).
    """

    UNALIGNED = -1
    ALIGNED_UNKNOWN = 0
