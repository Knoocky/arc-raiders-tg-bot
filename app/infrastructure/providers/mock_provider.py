from __future__ import annotations

from app.application.dto.event_definition_dto import EventDefinitionDTO
from app.application.dto.map_definition_dto import MapDefinitionDTO
from app.application.dto.scheduled_event_dto import ScheduledEventDTO
from app.infrastructure.providers.map_catalog_source import build_fallback_maps_catalog


class MockProvider:
    def __init__(
        self,
        *,
        schedule: list[ScheduledEventDTO] | None = None,
        events_catalog: list[EventDefinitionDTO] | None = None,
        maps_catalog: list[MapDefinitionDTO] | None = None,
    ) -> None:
        self._schedule = schedule or []
        self._events_catalog = events_catalog or []
        self._maps_catalog = maps_catalog if maps_catalog is not None else build_fallback_maps_catalog()

    async def fetch_schedule(self) -> list[ScheduledEventDTO]:
        return list(self._schedule)

    async def fetch_events_catalog(self) -> list[EventDefinitionDTO]:
        return list(self._events_catalog)

    async def fetch_maps_catalog(self) -> list[MapDefinitionDTO]:
        return list(self._maps_catalog)
