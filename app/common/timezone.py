from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.common.time_utils import ensure_utc

FALLBACK_TIMEZONE_NAME = "UTC+5"
FALLBACK_TIMEZONE = timezone(timedelta(hours=5), name=FALLBACK_TIMEZONE_NAME)


@dataclass(slots=True, frozen=True)
class ChatTimezoneContext:
    chat_id: int
    timezone_name: str | None
    timezone_info: timezone | ZoneInfo


def build_timezone_context(*, chat_id: int, timezone_name: str | None) -> ChatTimezoneContext:
    return ChatTimezoneContext(
        chat_id=chat_id,
        timezone_name=timezone_name,
        timezone_info=resolve_timezone(timezone_name),
    )


def resolve_timezone(timezone_name: str | None) -> timezone | ZoneInfo:
    if not timezone_name:
        return FALLBACK_TIMEZONE
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return FALLBACK_TIMEZONE


def convert_utc_to_chat_local(value: datetime, *, timezone_context: ChatTimezoneContext) -> datetime:
    return ensure_utc(value).astimezone(timezone_context.timezone_info)


def format_chat_local_time(value: datetime, *, timezone_context: ChatTimezoneContext) -> str:
    localized = convert_utc_to_chat_local(value, timezone_context=timezone_context)
    timezone_label = localized.tzname() or timezone_context.timezone_name or FALLBACK_TIMEZONE_NAME
    return f"{localized.strftime('%H:%M')} {timezone_label}"
