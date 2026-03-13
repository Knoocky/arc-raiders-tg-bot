import pytest

from app.application.exceptions import EntityNotFoundError
from app.application.services.catalog_resolver import CatalogResolver
from app.domain.models.event_definition import EventDefinition
from app.domain.models.map_definition import MapDefinition


class StubEventCatalogRepository:
    def __init__(self, items: list[EventDefinition]) -> None:
        self._items = items

    async def list_active(self) -> list[EventDefinition]:
        return list(self._items)


class StubMapCatalogRepository:
    def __init__(self, items: list[MapDefinition]) -> None:
        self._items = items

    async def list_active(self) -> list[MapDefinition]:
        return list(self._items)


@pytest.mark.asyncio
async def test_catalog_resolver_resolves_display_name_and_alias() -> None:
    resolver = CatalogResolver(
        event_catalog_repository=StubEventCatalogRepository(
            [
                EventDefinition(
                    id=1,
                    external_id="meteor",
                    canonical_name="meteor shower",
                    display_name="Meteor Shower",
                    aliases=("meteor rain",),
                )
            ]
        ),
        map_catalog_repository=StubMapCatalogRepository(
            [
                MapDefinition(
                    id=10,
                    external_id="blue-gate",
                    canonical_name="blue gate",
                    display_name="Blue Gate",
                    aliases=("bluegate",),
                )
            ]
        ),
    )

    event = await resolver.resolve_event_or_raise("  Meteor   Shower ")
    map_item = await resolver.resolve_map_or_raise("bluegate")

    assert event.display_name == "Meteor Shower"
    assert map_item.display_name == "Blue Gate"


@pytest.mark.asyncio
async def test_catalog_resolver_provides_suggestions_for_unknown_name() -> None:
    resolver = CatalogResolver(
        event_catalog_repository=StubEventCatalogRepository(
            [
                EventDefinition(
                    id=1,
                    external_id="meteor",
                    canonical_name="meteor shower",
                    display_name="Meteor Shower",
                )
            ]
        ),
        map_catalog_repository=StubMapCatalogRepository([]),
    )

    with pytest.raises(EntityNotFoundError) as exc_info:
        await resolver.resolve_event_or_raise("Meteorr shower")

    assert exc_info.value.suggestions == ["Meteor Shower"]

