from __future__ import annotations

from datetime import UTC, datetime


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def format_utc_time(value: datetime) -> str:
    return ensure_utc(value).strftime("%Y-%m-%d %H:%M UTC")


def minutes_until(starts_at: datetime, *, now: datetime) -> int:
    delta = ensure_utc(starts_at) - ensure_utc(now)
    return int(delta.total_seconds() // 60)


def format_countdown(starts_at: datetime, *, now: datetime) -> str:
    minutes = minutes_until(starts_at, now=now)
    if minutes <= 0:
        return "Now"
    if minutes < 60:
        return f"{minutes} min"

    hours, remaining_minutes = divmod(minutes, 60)
    if remaining_minutes == 0:
        return f"{hours} h"
    return f"{hours} h {remaining_minutes} min"

