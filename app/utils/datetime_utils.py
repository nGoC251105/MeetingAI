"""D11 serialization for UTC database values and offset-aware instants."""

from datetime import datetime, timezone


def serialize_datetime(value: datetime) -> str:
    """Return UTC ISO-8601; naive inputs must already represent stored UTC.

    MySQL connections are configured to UTC, including TIMESTAMP reads.
    This is not a parser for offset-free client input or local wall times.
    """
    if value.tzinfo is None or value.utcoffset() is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()
