from datetime import UTC, datetime, timedelta

from app.application.dto.event_definition_dto import EventDefinitionDTO
from app.application.dto.map_definition_dto import MapDefinitionDTO
from app.application.dto.scheduled_event_dto import ScheduledEventDTO
from app.bot.formatters.events_summary_formatter import format_events_summary
from app.infrastructure.providers.mock_provider import MockProvider


async def test_schedule_refresh_flow_persists_and_filters_events(app_factory) -> None:
    now = datetime(2026, 3, 11, 12, 0, tzinfo=UTC)
    app = await app_factory(
        MockProvider(
            events_catalog=[
                EventDefinitionDTO(
                    external_id="meteor",
                    canonical_name="meteor shower",
                    display_name="Meteor Shower",
                )
            ],
            maps_catalog=[
                MapDefinitionDTO(
                    external_id="blue-gate",
                    canonical_name="blue gate",
                    display_name="Blue Gate",
                )
            ],
            schedule=[
                ScheduledEventDTO(
                    source_id="schedule-1",
                    event_external_id="meteor",
                    event_canonical_name="meteor shower",
                    event_display_name="Meteor Shower",
                    map_external_id="blue-gate",
                    map_canonical_name="blue gate",
                    map_display_name="Blue Gate",
                    starts_at=now + timedelta(minutes=30),
                ),
                ScheduledEventDTO(
                    source_id="schedule-2",
                    event_external_id=None,
                    event_canonical_name="unknown event",
                    event_display_name="Unknown Event",
                    map_external_id=None,
                    map_canonical_name="unknown map",
                    map_display_name="Unknown Map",
                    starts_at=now + timedelta(minutes=45),
                ),
            ],
        )
    )

    await app.catalog_service.refresh_catalogs()
    await app.event_service.refresh_schedule()

    event = await app.catalog_resolver.resolve_event_or_raise("Meteor shower")
    map_item = await app.catalog_resolver.resolve_map_or_raise("Blue gate")
    filtered = await app.event_service.list_upcoming_events(
        now=now,
        event_catalog_id=event.id,
        map_catalog_id=map_item.id,
    )
    all_events = await app.event_service.list_upcoming_events(now=now)

    assert len(filtered) == 1
    assert filtered[0].event_display_name == "Meteor Shower"
    assert len(all_events) == 2
    assert any(item.event_catalog_id is None and item.map_catalog_id is None for item in all_events)


async def test_events_summary_includes_empty_known_event_groups(app_factory) -> None:
    now = datetime(2026, 3, 11, 12, 0, tzinfo=UTC)
    app = await app_factory(
        MockProvider(
            events_catalog=[
                EventDefinitionDTO(
                    external_id="meteor",
                    canonical_name="meteor shower",
                    display_name="Meteor Shower",
                ),
                EventDefinitionDTO(
                    external_id="fog",
                    canonical_name="deadly fog",
                    display_name="Deadly Fog",
                ),
            ],
            maps_catalog=[
                MapDefinitionDTO(
                    external_id="blue-gate",
                    canonical_name="blue gate",
                    display_name="Blue Gate",
                )
            ],
            schedule=[
                ScheduledEventDTO(
                    source_id="schedule-1",
                    event_external_id="meteor",
                    event_canonical_name="meteor shower",
                    event_display_name="Meteor Shower",
                    map_external_id="blue-gate",
                    map_canonical_name="blue gate",
                    map_display_name="Blue Gate",
                    starts_at=now + timedelta(minutes=30),
                )
            ],
        )
    )

    await app.catalog_service.refresh_catalogs()
    await app.event_service.refresh_schedule()

    groups, hidden = await app.event_service.list_events_summary(now=now)

    assert hidden == 0
    assert [group.event_display_name for group in groups] == ["Meteor Shower", "Deadly Fog"]
    assert groups[0].primary_line is not None
    assert groups[1].primary_line is None


async def test_events_summary_formatter_uses_chat_timezone(app_factory) -> None:
    now = datetime(2026, 3, 11, 12, 0, tzinfo=UTC)
    app = await app_factory(
        MockProvider(
            events_catalog=[
                EventDefinitionDTO(
                    external_id="meteor",
                    canonical_name="meteor shower",
                    display_name="Meteor Shower",
                )
            ],
            maps_catalog=[
                MapDefinitionDTO(
                    external_id="blue-gate",
                    canonical_name="blue gate",
                    display_name="Blue Gate",
                )
            ],
            schedule=[
                ScheduledEventDTO(
                    source_id="schedule-1",
                    event_external_id="meteor",
                    event_canonical_name="meteor shower",
                    event_display_name="Meteor Shower",
                    map_external_id="blue-gate",
                    map_canonical_name="blue gate",
                    map_display_name="Blue Gate",
                    starts_at=now + timedelta(minutes=30),
                )
            ],
        )
    )

    await app.catalog_service.refresh_catalogs()
    await app.event_service.refresh_schedule()
    await app.timezone_service.set_chat_timezone(chat_id=2001, timezone_name="Europe/Amsterdam")

    groups, _ = await app.event_service.list_events_summary(now=now)
    timezone_context = await app.timezone_service.get_chat_timezone(chat_id=2001)
    text = format_events_summary(groups, now=now, timezone_context=timezone_context)

    assert "<b>⏳ 13:30 CET - Blue Gate - через 30 мин</b>" in text
