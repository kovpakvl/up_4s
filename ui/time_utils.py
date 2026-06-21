from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any


MOSCOW_TZ = timezone(timedelta(hours=3), "MSK")


def parse_timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str) and value.strip():
        text = value.strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            try:
                dt = parsedate_to_datetime(text)
            except (TypeError, ValueError):
                return None
    else:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def to_moscow(value: Any) -> datetime | None:
    dt = parse_timestamp(value)
    if dt is None:
        return None
    return dt.astimezone(MOSCOW_TZ)


def format_moscow_datetime(value: Any) -> str:
    dt = to_moscow(value)
    if dt is None:
        return str(value or "")
    return f"{dt:%d.%m.%Y %H:%M} МСК"


def format_moscow_day(value: Any) -> str:
    dt = to_moscow(value)
    if dt is None:
        return ""
    return f"{dt:%d.%m.%Y}"


def format_moscow_time(value: Any) -> str:
    dt = to_moscow(value)
    if dt is None:
        return str(value or "")
    return f"{dt:%H:%M} МСК"


def seconds_since(value: Any) -> int | None:
    dt = parse_timestamp(value)
    if dt is None:
        return None
    return int((datetime.now(timezone.utc) - dt).total_seconds())
