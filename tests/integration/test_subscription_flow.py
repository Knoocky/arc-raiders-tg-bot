from app.application.dto.event_definition_dto import EventDefinitionDTO
from app.application.dto.map_definition_dto import MapDefinitionDTO
from app.infrastructure.providers.mock_provider import MockProvider


async def test_subscription_creation_and_removal_flow(app_factory) -> None:
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
        )
    )
    await app.catalog_service.refresh_catalogs()

    event = await app.catalog_resolver.resolve_event_or_raise("Meteor shower")
    map_item = await app.catalog_resolver.resolve_map_or_raise("Blue gate")

    _, created_all = await app.subscription_service.subscribe(chat_id=1001)
    _, created_map = await app.subscription_service.subscribe(chat_id=1001, map_catalog_id=map_item.id)
    _, created_event_map = await app.subscription_service.subscribe(
        chat_id=1001,
        event_catalog_id=event.id,
        map_catalog_id=map_item.id,
    )
    _, duplicate_created = await app.subscription_service.subscribe(
        chat_id=1001,
        event_catalog_id=event.id,
        map_catalog_id=map_item.id,
    )

    subscriptions = await app.subscription_service.list_subscriptions(chat_id=1001)
    removed_one = await app.subscription_service.unsubscribe(
        chat_id=1001,
        event_catalog_id=event.id,
        map_catalog_id=map_item.id,
    )
    removed_all = await app.subscription_service.unsubscribe_all(chat_id=1001)

    assert created_all is True
    assert created_map is True
    assert created_event_map is True
    assert duplicate_created is False
    assert len(subscriptions) == 3
    assert removed_one == 1
    assert removed_all == 2

