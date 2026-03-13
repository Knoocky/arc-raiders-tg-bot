from __future__ import annotations

from datetime import datetime

from app.application.services.event_service import EventService
from app.application.services.timezone_service import TimezoneService
from app.bot.formatters.events_summary_formatter import format_events_summary
from app.common.time_utils import utc_now


async def build_events_summary_text(
    *,
    chat_id: int,
    event_service: EventService,
    timezone_service: TimezoneService,
    event_catalog_id: int | None = None,
    map_catalog_id: int | None = None,
    now: datetime | None = None,
    max_future_lines_per_group: int | None = None,
) -> str:
    current_time = now or utc_now()
    timezone_context = await timezone_service.get_chat_timezone(chat_id=chat_id)
    groups, hidden_groups_count = await event_service.list_events_summary(
        now=current_time,
        event_catalog_id=event_catalog_id,
        map_catalog_id=map_catalog_id,
        **(
            {}
            if max_future_lines_per_group is None
            else {"max_future_lines_per_group": max_future_lines_per_group}
        ),
    )
    return format_events_summary(
        groups,
        now=current_time,
        timezone_context=timezone_context,
        hidden_groups_count=hidden_groups_count,
    )
