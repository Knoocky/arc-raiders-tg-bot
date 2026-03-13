from app.application.dto.event_definition_dto import EventDefinitionDTO
from app.application.dto.map_definition_dto import MapDefinitionDTO
from app.infrastructure.providers.mock_provider import MockProvider


async def test_catalog_refresh_flow_persists_catalogs(app_factory) -> None:
    app = await app_factory(
        MockProvider(
            events_catalog=[
                EventDefinitionDTO(
                    external_id="meteor",
                    canonical_name="meteor shower",
                    display_name="Meteor Shower",
                    aliases=["meteor rain"],
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

    events_catalog = await app.catalog_service.list_events_catalog()
    maps_catalog = await app.catalog_service.list_maps_catalog()

    assert [item.display_name for item in events_catalog] == ["Meteor Shower"]
    assert [item.display_name for item in maps_catalog] == ["Blue Gate"]


async def test_catalog_refresh_flow_is_agnostic_to_map_catalog_source(app_factory) -> None:
    app = await app_factory(
        MockProvider(
            events_catalog=[
                EventDefinitionDTO(
                    external_id="meteor",
                    canonical_name="meteor shower",
                    display_name="Meteor Shower",
                )
            ],
        )
    )

    await app.catalog_service.refresh_catalogs()

    maps_catalog = await app.catalog_service.list_maps_catalog()

    assert [item.display_name for item in maps_catalog] == [
        "Blue Gate",
        "Buried City",
        "Dam",
        "Spaceport",
        "Stella Montis",
    ]
