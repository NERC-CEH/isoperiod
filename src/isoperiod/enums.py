from enum import IntEnum


class Step(IntEnum):
    """The fundamental units of a Period.

    A Period's duration is always some multiplier of one of these steps, e.g. a 15-minute period is 900 seconds,
    a 1-year period is 12 months.
    """

    MICROSECONDS = 1
    SECONDS = 2
    MONTHS = 3
