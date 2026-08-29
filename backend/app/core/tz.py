"""Timezone helpers. Storage is naive UTC (ADR-0014); these convert to a user's
local wall-clock only where a *day* boundary matters (analytics buckets)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def resolve(name: str) -> ZoneInfo:
    """Return the ZoneInfo for ``name`` or raise ``ValueError`` for a bad name."""
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"unknown timezone: {name!r}") from exc


def validate(name: str) -> str:
    resolve(name)
    return name


def today(name: str) -> date:
    """The current calendar date in the given zone."""
    return datetime.now(resolve(name)).date()


def local_date(naive_utc: datetime, name: str) -> date:
    """The calendar date a stored (naive-UTC) timestamp falls on locally."""
    return naive_utc.replace(tzinfo=UTC).astimezone(resolve(name)).date()
