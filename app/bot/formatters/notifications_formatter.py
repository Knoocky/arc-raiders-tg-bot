from __future__ import annotations

from datetime import datetime

from app.common.timezone import ChatTimezoneContext, format_chat_local_time
from app.domain.models.scheduled_event import ScheduledEvent


def format_offsets(offsets: list[int]) -> str:
    if not offsets:
        return "No notification offsets configured."
    return "Notification offsets: " + ", ".join(str(offset) for offset in offsets) + " min"


def format_notification_message(
    event: ScheduledEvent,
    minutes_before: int,
    now: datetime,
    timezone_context: ChatTimezoneContext,
) -> str:
    del minutes_before
    del now
    return (
        f"{event.event_display_name} - {event.map_display_name}\n"
        f"Starts: {format_chat_local_time(event.starts_at, timezone_context=timezone_context)}"
    )
