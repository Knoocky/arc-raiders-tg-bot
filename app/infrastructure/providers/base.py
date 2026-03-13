from __future__ import annotations

from typing import Protocol

from app.application.dto.event_definition_dto import EventDefinitionDTO
from app.application.dto.map_definition_dto import MapDefinitionDTO
from app.application.dto.scheduled_event_dto import ScheduledEventDTO


class ArcEventsProvider(Protocol):
    async def fetch_schedule(self) -> list[ScheduledEventDTO]:
        ...

    async def fetch_events_catalog(self) -> list[EventDefinitionDTO]:
        ...

    async def fetch_maps_catalog(self) -> list[MapDefinitionDTO]:
        ...

