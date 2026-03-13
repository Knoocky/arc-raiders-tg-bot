from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.application.dto.event_definition_dto import EventDefinitionDTO
from app.application.dto.map_definition_dto import MapDefinitionDTO
from app.application.dto.scheduled_event_dto import ScheduledEventDTO
from app.bot.presenters.events_presenter import build_events_summary_text
from app.bot.presenters.subscriptions_presenter import build_subscriptions_overview_text
from app.common.time_utils import utc_now
from app.infrastructure.providers.mock_provider import MockProvider


def _build_button_texts(screen) -> list[str]:
    return [button.text for row in screen.keyboard.inline_keyboard for button in row]


def _build_callback_data(screen) -> list[str]:
    return [button.callback_data or "" for row in screen.keyboard.inline_keyboard for button in row]


def _group_lines(text: str, header: str) -> list[str]:
    blocks = text.split("\n\n")
    group_block = next(block for block in blocks if block.startswith(f"{header}:"))
    return [line for line in group_block.splitlines()[1:] if line.strip()]


def _build_provider(*, total_events: int = 2, total_maps: int = 2) -> MockProvider:
    now = datetime(2026, 3, 11, 12, 0, tzinfo=UTC)
    events_catalog = [
        EventDefinitionDTO(
            external_id=f"event-{index}",
            canonical_name=f"event {index}",
            display_name=f"Event {index}",
        )
        for index in range(total_events)
    ]
    maps_catalog = [
        MapDefinitionDTO(
            external_id=f"map-{index}",
            canonical_name=f"map {index}",
            display_name=f"Map {index}",
        )
        for index in range(total_maps)
    ]
    schedule = [
        ScheduledEventDTO(
            source_id="schedule-1",
            event_external_id="event-0",
            event_canonical_name="event 0",
            event_display_name="Event 0",
            map_external_id="map-0",
            map_canonical_name="map 0",
            map_display_name="Map 0",
            starts_at=now + timedelta(minutes=15),
            ends_at=now + timedelta(minutes=45),
        ),
        ScheduledEventDTO(
            source_id="schedule-2",
            event_external_id="event-1" if total_events > 1 else "event-0",
            event_canonical_name="event 1" if total_events > 1 else "event 0",
            event_display_name="Event 1" if total_events > 1 else "Event 0",
            map_external_id="map-1" if total_maps > 1 else "map-0",
            map_canonical_name="map 1" if total_maps > 1 else "map 0",
            map_display_name="Map 1" if total_maps > 1 else "Map 0",
            starts_at=now + timedelta(minutes=60),
            ends_at=now + timedelta(minutes=90),
        ),
    ]
    return MockProvider(
        events_catalog=events_catalog,
        maps_catalog=maps_catalog,
        schedule=schedule,
    )


async def test_menu_subscribe_flow_supports_any_map_and_duplicate_protection(app_factory) -> None:
    app = await app_factory(_build_provider())
    await app.catalog_service.refresh_catalogs()

    events = await app.catalog_service.list_events_catalog()
    event = events[0]

    events_screen = await app.menu_controller.build_subscribe_events_screen(page=0)
    maps_screen = await app.menu_controller.build_subscribe_maps_screen(event_id=event.id, event_page=0, page=0)
    created_screen = await app.menu_controller.create_event_subscription(
        chat_id=1001,
        event_id=event.id,
        event_page=0,
        map_page=0,
        map_id=None,
    )
    duplicate_screen = await app.menu_controller.create_event_subscription(
        chat_id=1001,
        event_id=event.id,
        event_page=0,
        map_page=0,
        map_id=None,
    )
    subscriptions = await app.subscription_service.list_subscriptions(chat_id=1001)

    assert "Event 0" in _build_button_texts(events_screen)
    assert "Любая карта" in _build_button_texts(maps_screen)
    assert created_screen.text == "Watching event Event 0."
    assert duplicate_screen.text == "Already watching event Event 0."
    assert len(subscriptions) == 1
    assert subscriptions[0].event_display_name == "Event 0"
    assert subscriptions[0].map_display_name is None


async def test_menu_unsubscribe_flow_supports_single_subscription_and_remove_all(app_factory) -> None:
    app = await app_factory(_build_provider())
    await app.catalog_service.refresh_catalogs()

    event, other_event = await app.catalog_service.list_events_catalog()
    map_item = (await app.catalog_service.list_maps_catalog())[0]
    await app.subscription_service.subscribe(chat_id=2001, event_catalog_id=event.id, map_catalog_id=map_item.id)
    await app.subscription_service.subscribe(chat_id=2001, event_catalog_id=other_event.id)
    subscriptions = await app.subscription_service.list_subscriptions(chat_id=2001)

    unsubscribe_screen = await app.menu_controller.build_unsubscribe_screen(chat_id=2001, page=0)
    remove_one_screen = await app.menu_controller.remove_subscription(
        chat_id=2001,
        subscription_id=subscriptions[0].subscription_id,
        page=0,
    )
    remove_all_screen = await app.menu_controller.remove_all_subscriptions(chat_id=2001, page=0)
    remaining = await app.subscription_service.list_subscriptions(chat_id=2001)

    assert "Отписаться от всех" in _build_button_texts(unsubscribe_screen)
    assert remove_one_screen.text.startswith("Подписка удалена:")
    assert remove_all_screen.text == "Все подписки удалены."
    assert remaining == []


async def test_menu_notification_flow_supports_presets_custom_input_and_reset(app_factory) -> None:
    app = await app_factory(_build_provider())

    await app.menu_controller.add_notification_offset(chat_id=3001, minutes=15)
    await app.menu_controller.add_notification_offset(chat_id=3001, minutes=30)
    await app.menu_controller.remove_notification_offset(chat_id=3001, minutes=15)
    await app.menu_controller.apply_custom_notification_input(chat_id=3001, raw_text="5 15 45")
    await app.menu_controller.apply_custom_notification_input(chat_id=3001, raw_text="/notify add 90")
    offsets_before_clear = await app.notification_service.list_offsets(chat_id=3001)
    clear_screen = await app.menu_controller.clear_notification_offsets(chat_id=3001)
    offsets = await app.notification_service.list_offsets(chat_id=3001)

    assert offsets_before_clear == [90, 45, 15, 5]
    assert clear_screen.text.endswith("Все смещения уведомлений сброшены.")
    assert offsets == []


async def test_menu_schedule_and_list_screens_reuse_existing_presenters(app_factory) -> None:
    app = await app_factory(_build_provider())
    await app.catalog_service.refresh_catalogs()
    await app.event_service.refresh_schedule()

    event = (await app.catalog_service.list_events_catalog())[0]
    await app.subscription_service.subscribe(chat_id=4001, event_catalog_id=event.id)
    await app.notification_service.replace_offsets(chat_id=4001, minutes=(30, 15))

    all_schedule_screen = await app.menu_controller.build_all_schedule_screen(chat_id=4001)
    event_schedule_screen = await app.menu_controller.build_event_schedule_screen(
        chat_id=4001,
        event_id=event.id,
        page=0,
    )
    subscriptions_screen = await app.menu_controller.build_my_subscriptions_screen(chat_id=4001)

    assert all_schedule_screen.text == await build_events_summary_text(
        chat_id=4001,
        event_service=app.event_service,
        timezone_service=app.timezone_service,
    )
    assert event_schedule_screen.text == await build_events_summary_text(
        chat_id=4001,
        event_service=app.event_service,
        timezone_service=app.timezone_service,
        event_catalog_id=event.id,
    )
    assert subscriptions_screen.text == await build_subscriptions_overview_text(
        chat_id=4001,
        subscription_service=app.subscription_service,
        notification_service=app.notification_service,
    )


async def test_full_schedule_screen_limits_group_details_but_event_specific_keeps_extended_view(app_factory) -> None:
    now = utc_now().replace(second=0, microsecond=0)
    app = await app_factory(
        MockProvider(
            events_catalog=[
                EventDefinitionDTO(
                    external_id="event-0",
                    canonical_name="event 0",
                    display_name="Event 0",
                )
            ],
            maps_catalog=[
                MapDefinitionDTO(external_id=f"map-{index}", canonical_name=f"map {index}", display_name=f"Map {index}")
                for index in range(4)
            ],
            schedule=[
                ScheduledEventDTO(
                    source_id=f"schedule-{index}",
                    event_external_id="event-0",
                    event_canonical_name="event 0",
                    event_display_name="Event 0",
                    map_external_id=f"map-{index}",
                    map_canonical_name=f"map {index}",
                    map_display_name=f"Map {index}",
                    starts_at=now + timedelta(minutes=15 * (index + 1)),
                    ends_at=now + timedelta(minutes=15 * (index + 2)),
                )
                for index in range(4)
            ],
        )
    )
    await app.catalog_service.refresh_catalogs()
    await app.event_service.refresh_schedule()
    event = (await app.catalog_service.list_events_catalog())[0]

    full_schedule_screen = await app.menu_controller.build_all_schedule_screen(chat_id=4101)
    event_schedule_screen = await app.menu_controller.build_event_schedule_screen(
        chat_id=4101,
        event_id=event.id,
        page=0,
    )

    assert len(_group_lines(full_schedule_screen.text, "Event 0")) == 2
    assert len(_group_lines(event_schedule_screen.text, "Event 0")) == 4


async def test_menu_lists_are_paginated_and_callback_data_remains_short(app_factory) -> None:
    app = await app_factory(_build_provider(total_events=10, total_maps=10))
    await app.catalog_service.refresh_catalogs()
    first_event = (await app.catalog_service.list_events_catalog())[0]

    for index, event in enumerate(await app.catalog_service.list_events_catalog()):
        if index < 9:
            await app.subscription_service.subscribe(chat_id=5001, event_catalog_id=event.id)

    first_events_screen = await app.menu_controller.build_subscribe_events_screen(page=0)
    second_events_screen = await app.menu_controller.build_subscribe_events_screen(page=1)
    maps_screen = await app.menu_controller.build_subscribe_maps_screen(event_id=first_event.id, event_page=0, page=1)
    subscriptions_screen = await app.menu_controller.build_unsubscribe_screen(chat_id=5001, page=1)

    assert "Далее" in _build_button_texts(first_events_screen)
    assert "Назад" in _build_button_texts(second_events_screen)
    assert "Далее" in _build_button_texts(maps_screen) or "Назад" in _build_button_texts(maps_screen)
    assert "Назад" in _build_button_texts(subscriptions_screen)
    assert max(len(data) for data in _build_callback_data(first_events_screen)) < 64
    assert max(len(data) for data in _build_callback_data(maps_screen)) < 64
    assert max(len(data) for data in _build_callback_data(subscriptions_screen)) < 64
