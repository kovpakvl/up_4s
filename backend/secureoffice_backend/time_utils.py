from __future__ import annotations

from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any
from zoneinfo import ZoneInfo


MOSCOW_TZ = ZoneInfo("Europe/Moscow")


def parse_datetime(value: Any) -> datetime | None:
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
    dt = parse_datetime(value)
    if dt is None:
        return None
    return dt.astimezone(MOSCOW_TZ).replace(microsecond=0)


def iso_moscow(value: Any) -> str:
    dt = to_moscow(value)
    return dt.isoformat() if dt else str(value or "")


def format_moscow_datetime(value: Any) -> str:
    dt = to_moscow(value)
    if dt is None:
        return str(value or "")
    return f"{dt:%d.%m.%Y %H:%M} МСК"
