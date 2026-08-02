from datetime import UTC, datetime

import uuid6


def utc_now() -> datetime:
    """Returns the current UTC time."""
    return datetime.now(UTC)


def generate_uuid() -> str:
    """Generates a UUIDv7 string."""
    return str(uuid6.uuid7())
