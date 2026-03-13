from datetime import UTC, datetime, timedelta

from app.application.dto.event_definition_dto import EventDefinitionDTO
from app.application.dto.map_definition_dto import MapDefinitionDTO
from app.application.dto.scheduled_event_dto import ScheduledEventDTO
from app.infrastructure.providers.mock_provider import MockProvider


async def test_notification_dispatch_flow(app_factory) -> None:
    now = datetime(2026, 3, 11, 12, 0, 30, tzinfo=UTC)
    starts_at = now + timedelta(minutes=29, seconds=30)
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
                    starts_at=starts_at,
                )
            ],
        )
    )
    await app.catalog_service.refresh_catalogs()
    await app.event_service.refresh_schedule()

    event = await app.catalog_resolver.resolve_event_or_raise("Meteor shower")
    await app.subscription_service.subscribe(chat_id=1001, event_catalog_id=event.id)
    await app.notification_service.replace_offsets(chat_id=1001, minutes=[30])

    sent_count = await app.notification_service.dispatch_due_notifications(now=now)

    assert sent_count == 1
    assert len(app.sender.messages) == 1
    assert app.sender.messages[0][0] == 1001
    assert "Meteor Shower - Blue Gate" in app.sender.messages[0][1]
    assert "Starts: 17:30 UTC+5" in app.sender.messages[0][1]
    assert "In:" not in app.sender.messages[0][1]
    assert "Notification offset:" not in app.sender.messages[0][1]


async def test_notification_dispatch_prevents_duplicates(app_factory) -> None:
    now = datetime(2026, 3, 11, 12, 0, 30, tzinfo=UTC)
    starts_at = now + timedelta(minutes=29, seconds=30)
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
                    starts_at=starts_at,
                )
            ],
        )
    )
    await app.catalog_service.refresh_catalogs()
    await app.event_service.refresh_schedule()

    await app.subscription_service.subscribe(chat_id=1001)
    await app.notification_service.replace_offsets(chat_id=1001, minutes=[30])

    first_run = await app.notification_service.dispatch_due_notifications(now=now)
    second_run = await app.notification_service.dispatch_due_notifications(now=now)

    assert first_run == 1
    assert second_run == 0
    assert len(app.sender.messages) == 1


async def test_notification_dispatch_uses_saved_chat_timezone(app_factory) -> None:
    now = datetime(2026, 3, 11, 12, 0, 30, tzinfo=UTC)
    starts_at = now + timedelta(minutes=29, seconds=30)
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
                    starts_at=starts_at,
                )
            ],
        )
    )
    await app.catalog_service.refresh_catalogs()
    await app.event_service.refresh_schedule()

    await app.timezone_service.set_chat_timezone(chat_id=1001, timezone_name="Europe/Amsterdam")
    await app.subscription_service.subscribe(chat_id=1001)
    await app.notification_service.replace_offsets(chat_id=1001, minutes=[30])

    sent_count = await app.notification_service.dispatch_due_notifications(now=now)

    assert sent_count == 1
    assert "Starts: 13:30 CET" in app.sender.messages[0][1]
