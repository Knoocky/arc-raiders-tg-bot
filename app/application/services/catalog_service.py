from __future__ import annotations

import asyncio

from app.domain.models.event_definition import EventDefinition
from app.domain.models.map_definition import MapDefinition
from app.infrastructure.persistence.repositories.event_catalog_repository import EventCatalogRepository
from app.infrastructure.persistence.repositories.map_catalog_repository import MapCatalogRepository
from app.infrastructure.providers.base import ArcEventsProvider


class CatalogService:
    def __init__(
        self,
        *,
        provider: ArcEventsProvider,
        event_catalog_repository: EventCatalogRepository,
        map_catalog_repository: MapCatalogRepository,
    ) -> None:
        self._provider = provider
        self._event_catalog_repository = event_catalog_repository
        self._map_catalog_repository = map_catalog_repository

    async def refresh_catalogs(self) -> tuple[list[EventDefinition], list[MapDefinition]]:
        events_catalog, maps_catalog = await asyncio.gather(
            self._provider.fetch_events_catalog(),
            self._provider.fetch_maps_catalog(),
        )
        events = await self._event_catalog_repository.upsert_many(events_catalog)
        maps = await self._map_catalog_repository.upsert_many(maps_catalog)
        return events, maps

    async def list_events_catalog(self) -> list[EventDefinition]:
        return await self._event_catalog_repository.list_active()

    async def list_maps_catalog(self) -> list[MapDefinition]:
        return await self._map_catalog_repository.list_active()

    async def get_event_by_id(self, *, event_id: int) -> EventDefinition | None:
        return await self._event_catalog_repository.get_by_id(event_id)

    async def get_map_by_id(self, *, map_id: int) -> MapDefinition | None:
        return await self._map_catalog_repository.get_by_id(map_id)
