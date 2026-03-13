from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.bot.formatters.notifications_formatter import format_notification_message
from app.common.timezone import build_timezone_context
from app.domain.models.scheduled_event import ScheduledEvent


def test_notification_formatter_uses_chat_timezone_for_absolute_time() -> None:
    now = datetime(2026, 3, 11, 18, 0, tzinfo=UTC)
    event = ScheduledEvent(
        id=1,
        source_id="event-1",
        event_catalog_id=1,
        map_catalog_id=1,
        event_display_name="Meteor Shower",
        map_display_name="Blue Gate",
        starts_at=now + timedelta(minutes=30),
    )

    text = format_notification_message(
        event,
        30,
        now,
        build_timezone_context(chat_id=1, timezone_name="Europe/Amsterdam"),
    )

    assert "Starts: 19:30 CET" in text
    assert "In:" not in text
    assert "Notification offset:" not in text


def test_notification_formatter_keeps_only_title_and_start_time() -> None:
    now = datetime(2026, 3, 11, 18, 0, tzinfo=UTC)
    event = ScheduledEvent(
        id=1,
        source_id="event-1",
        event_catalog_id=1,
        map_catalog_id=1,
        event_display_name="Meteor Shower",
        map_display_name="Blue Gate",
        starts_at=now + timedelta(minutes=42),
    )

    utc_plus_five_text = format_notification_message(
        event,
        42,
        now,
        build_timezone_context(chat_id=1, timezone_name=None),
    )
    amsterdam_text = format_notification_message(
        event,
        42,
        now,
        build_timezone_context(chat_id=1, timezone_name="Europe/Amsterdam"),
    )

    assert utc_plus_five_text == "Meteor Shower - Blue Gate\nStarts: 23:42 UTC+5"
    assert amsterdam_text == "Meteor Shower - Blue Gate\nStarts: 19:42 CET"
