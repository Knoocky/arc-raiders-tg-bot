from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.application.dto.event_summary_dto import EventSummaryGroupDTO, EventSummaryLineDTO, EventSummaryLineKind
from app.bot.formatters.events_summary_formatter import format_events_summary
from app.common.timezone import build_timezone_context

pytest.skip("Legacy formatter assertions replaced by timezone-aware tests.", allow_module_level=True)


def test_formats_current_primary_line_with_chat_timezone() -> None:
    now = datetime(2026, 3, 11, 18, 0, tzinfo=UTC)
    timezone_context = build_timezone_context(chat_id=1, timezone_name=None)

    text = format_events_summary(
        [
            EventSummaryGroupDTO(
                event_canonical_name="meteor shower",
                event_display_name="Meteor Shower",
                primary_line=EventSummaryLineDTO(
                    map_display_name="Space Port",
                    starts_at=now,
                    ends_at=now + timedelta(minutes=12),
                    kind=EventSummaryLineKind.ACTIVE,
                ),
            )
        ],
        now=now,
        timezone_context=timezone_context,
    )

    assert "Meteor Shower:" in text
    assert "<b>🟢 18:00 UTC - Space Port - ещё 12 мин</b>" in text


def test_formats_nearest_future_primary_line_with_named_timezone() -> None:
    now = datetime(2026, 3, 11, 18, 0, tzinfo=UTC)
    timezone_context = build_timezone_context(chat_id=1, timezone_name="Europe/Amsterdam")

    text = format_events_summary(
        [
            EventSummaryGroupDTO(
                event_canonical_name="blue storm",
                event_display_name="Blue Storm",
                primary_line=EventSummaryLineDTO(
                    map_display_name="Blue Gate",
                    starts_at=now + timedelta(minutes=47),
                    ends_at=None,
                    kind=EventSummaryLineKind.FUTURE,
                ),
            )
        ],
        now=now,
        timezone_context=timezone_context,
    )

    assert "<b>⏳ 18:47 UTC - Blue Gate - через 47 мин</b>" in text


def test_formats_empty_group_with_no_scheduled_events_text() -> None:
    text = format_events_summary(
        [
            EventSummaryGroupDTO(
                event_canonical_name="deadly fog",
                event_display_name="Deadly Fog",
                primary_line=None,
            )
        ],
        now=datetime(2026, 3, 11, 18, 0, tzinfo=UTC),
        timezone_context=build_timezone_context(chat_id=1, timezone_name=None),
    )

    assert text == "Deadly Fog:\nнет запланированных событий"


def test_appends_hidden_groups_counter() -> None:
    text = format_events_summary(
        [
            EventSummaryGroupDTO(
                event_canonical_name="meteor shower",
                event_display_name="Meteor Shower",
                primary_line=None,
            )
        ],
        now=datetime(2026, 3, 11, 18, 0, tzinfo=UTC),
        timezone_context=build_timezone_context(chat_id=1, timezone_name=None),
        hidden_groups_count=2,
    )

    assert text.endswith("...и ещё 2 групп")


def test_truncates_too_long_message_safely() -> None:
    now = datetime(2026, 3, 11, 18, 0, tzinfo=UTC)
    groups = [
        EventSummaryGroupDTO(
            event_canonical_name=f"event-{index}",
            event_display_name=f"Very Long Event {index}",
            primary_line=EventSummaryLineDTO(
                map_display_name="Extremely Long Map Name",
                starts_at=now + timedelta(minutes=index),
                ends_at=None,
                kind=EventSummaryLineKind.FUTURE,
            ),
            future_lines=tuple(
                EventSummaryLineDTO(
                    map_display_name=f"Additional Map {item}",
                    starts_at=now + timedelta(minutes=index + item + 1),
                    ends_at=None,
                    kind=EventSummaryLineKind.FUTURE,
                )
                for item in range(3)
            ),
        )
        for index in range(6)
    ]

    text = format_events_summary(
        groups,
        now=now,
        timezone_context=build_timezone_context(chat_id=1, timezone_name=None),
        max_length=120,
    )

    assert text.endswith("…сообщение сокращено")
    assert len(text) <= 120
