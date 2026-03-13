from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.application.services.event_summary_service import EventSummaryService
from app.domain.models.event_definition import EventDefinition
from app.domain.models.scheduled_event import ScheduledEvent


def test_selects_active_event_that_ends_first() -> None:
    now = datetime(2026, 3, 11, 18, 0, tzinfo=UTC)

    groups, hidden = EventSummaryService.build_groups(
        scheduled_events=[
            _scheduled_event(
                source_id="later-active",
                event_catalog_id=1,
                event_display_name="Meteor Shower",
                map_display_name="Blue Gate",
                starts_at=now - timedelta(minutes=20),
                ends_at=now + timedelta(minutes=40),
            ),
            _scheduled_event(
                source_id="earlier-active",
                event_catalog_id=1,
                event_display_name="Meteor Shower",
                map_display_name="Space Port",
                starts_at=now - timedelta(minutes=10),
                ends_at=now + timedelta(minutes=15),
            ),
        ],
        known_events=[_event_definition(1, "meteor shower", "Meteor Shower")],
        now=now,
    )

    assert hidden == 0
    assert groups[0].primary_line is not None
    assert groups[0].primary_line.map_display_name == "Space Port"
    assert groups[0].primary_line.kind.value == "active"


def test_selects_nearest_future_event_when_no_active_event_exists() -> None:
    now = datetime(2026, 3, 11, 18, 0, tzinfo=UTC)

    groups, _ = EventSummaryService.build_groups(
        scheduled_events=[
            _scheduled_event(
                source_id="future-2",
                event_catalog_id=1,
                event_display_name="Meteor Shower",
                map_display_name="Dam",
                starts_at=now + timedelta(hours=2),
            ),
            _scheduled_event(
                source_id="future-1",
                event_catalog_id=1,
                event_display_name="Meteor Shower",
                map_display_name="Blue Gate",
                starts_at=now + timedelta(minutes=30),
            ),
        ],
        known_events=[_event_definition(1, "meteor shower", "Meteor Shower")],
        now=now,
    )

    assert groups[0].primary_line is not None
    assert groups[0].primary_line.map_display_name == "Blue Gate"
    assert groups[0].primary_line.kind.value == "future"


def test_limits_additional_future_events_to_three() -> None:
    now = datetime(2026, 3, 11, 18, 0, tzinfo=UTC)

    groups, _ = EventSummaryService.build_groups(
        scheduled_events=[
            _scheduled_event(
                source_id=f"future-{index}",
                event_catalog_id=1,
                event_display_name="Meteor Shower",
                map_display_name=f"Map {index}",
                starts_at=now + timedelta(minutes=15 * index),
            )
            for index in range(1, 6)
        ],
        known_events=[_event_definition(1, "meteor shower", "Meteor Shower")],
        now=now,
    )

    assert groups[0].primary_line is not None
    assert groups[0].primary_line.map_display_name == "Map 1"
    assert [line.map_display_name for line in groups[0].future_lines] == ["Map 2", "Map 3", "Map 4"]


def test_supports_custom_limit_for_future_lines_per_group() -> None:
    now = datetime(2026, 3, 11, 18, 0, tzinfo=UTC)

    groups, _ = EventSummaryService.build_groups(
        scheduled_events=[
            _scheduled_event(
                source_id=f"future-{index}",
                event_catalog_id=1,
                event_display_name="Meteor Shower",
                map_display_name=f"Map {index}",
                starts_at=now + timedelta(minutes=15 * index),
            )
            for index in range(1, 6)
        ],
        known_events=[_event_definition(1, "meteor shower", "Meteor Shower")],
        now=now,
        max_future_lines_per_group=1,
    )

    assert groups[0].primary_line is not None
    assert groups[0].primary_line.map_display_name == "Map 1"
    assert [line.map_display_name for line in groups[0].future_lines] == ["Map 2"]


def test_empty_group_is_kept_when_catalog_has_event_without_schedule() -> None:
    now = datetime(2026, 3, 11, 18, 0, tzinfo=UTC)

    groups, _ = EventSummaryService.build_groups(
        scheduled_events=[],
        known_events=[_event_definition(1, "deadly fog", "Deadly Fog")],
        now=now,
    )

    assert len(groups) == 1
    assert groups[0].event_display_name == "Deadly Fog"
    assert groups[0].primary_line is None


def test_empty_groups_are_sorted_after_non_empty_groups() -> None:
    now = datetime(2026, 3, 11, 18, 0, tzinfo=UTC)

    groups, _ = EventSummaryService.build_groups(
        scheduled_events=[
            _scheduled_event(
                source_id="scheduled",
                event_catalog_id=1,
                event_display_name="Blue Storm",
                map_display_name="Blue Gate",
                starts_at=now + timedelta(minutes=20),
            )
        ],
        known_events=[
            _event_definition(1, "blue storm", "Blue Storm"),
            _event_definition(2, "deadly fog", "Deadly Fog"),
        ],
        now=now,
    )

    assert [group.event_display_name for group in groups] == ["Blue Storm", "Deadly Fog"]


def test_returns_all_groups_by_default() -> None:
    now = datetime(2026, 3, 11, 18, 0, tzinfo=UTC)
    scheduled_events = []
    known_events = []
    for index in range(7):
        known_events.append(_event_definition(index + 1, f"event-{index}", f"Event {index}"))
        scheduled_events.append(
            _scheduled_event(
                source_id=f"scheduled-{index}",
                event_catalog_id=index + 1,
                event_display_name=f"Event {index}",
                map_display_name="Blue Gate",
                starts_at=now + timedelta(minutes=index + 1),
            )
        )

    groups, hidden = EventSummaryService.build_groups(
        scheduled_events=scheduled_events,
        known_events=known_events,
        now=now,
    )

    assert len(groups) == 7
    assert hidden == 0


def test_supports_optional_group_limit_and_reports_hidden_count() -> None:
    now = datetime(2026, 3, 11, 18, 0, tzinfo=UTC)
    scheduled_events = []
    known_events = []
    for index in range(7):
        known_events.append(_event_definition(index + 1, f"event-{index}", f"Event {index}"))
        scheduled_events.append(
            _scheduled_event(
                source_id=f"scheduled-{index}",
                event_catalog_id=index + 1,
                event_display_name=f"Event {index}",
                map_display_name="Blue Gate",
                starts_at=now + timedelta(minutes=index + 1),
            )
        )

    groups, hidden = EventSummaryService.build_groups(
        scheduled_events=scheduled_events,
        known_events=known_events,
        now=now,
        max_groups=6,
    )

    assert len(groups) == 6
    assert hidden == 1


def test_event_without_ends_at_is_not_considered_active() -> None:
    now = datetime(2026, 3, 11, 18, 0, tzinfo=UTC)

    groups, _ = EventSummaryService.build_groups(
        scheduled_events=[
            _scheduled_event(
                source_id="missing-end",
                event_catalog_id=1,
                event_display_name="Meteor Shower",
                map_display_name="Blue Gate",
                starts_at=now - timedelta(minutes=10),
                ends_at=None,
            ),
            _scheduled_event(
                source_id="future",
                event_catalog_id=1,
                event_display_name="Meteor Shower",
                map_display_name="Dam",
                starts_at=now + timedelta(minutes=25),
            ),
        ],
        known_events=[_event_definition(1, "meteor shower", "Meteor Shower")],
        now=now,
    )

    assert groups[0].primary_line is not None
    assert groups[0].primary_line.map_display_name == "Dam"
    assert groups[0].primary_line.kind.value == "future"


def _event_definition(event_id: int, canonical_name: str, display_name: str) -> EventDefinition:
    return EventDefinition(
        id=event_id,
        external_id=None,
        canonical_name=canonical_name,
        display_name=display_name,
    )


def _scheduled_event(
    *,
    source_id: str,
    event_catalog_id: int | None,
    event_display_name: str,
    map_display_name: str,
    starts_at: datetime,
    ends_at: datetime | None = None,
) -> ScheduledEvent:
    return ScheduledEvent(
        id=None,
        source_id=source_id,
        event_catalog_id=event_catalog_id,
        map_catalog_id=None,
        event_display_name=event_display_name,
        map_display_name=map_display_name,
        starts_at=starts_at,
        ends_at=ends_at,
    )
