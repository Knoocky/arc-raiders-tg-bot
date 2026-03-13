from __future__ import annotations

from datetime import datetime

from app.application.dto.event_summary_dto import EventSummaryGroupDTO
from app.application.services.event_summary_service import EventSummaryService
from app.common.time_utils import utc_now
from app.domain.models.event_definition import EventDefinition
from app.domain.models.scheduled_event import ScheduledEvent
from app.infrastructure.persistence.repositories.event_catalog_repository import EventCatalogRepository
from app.infrastructure.persistence.repositories.map_catalog_repository import MapCatalogRepository
from app.infrastructure.persistence.repositories.scheduled_events_repository import ScheduledEventsRepository
from app.infrastructure.providers.base import ArcEventsProvider


class EventService:
    def __init__(
        self,
        *,
        provider: ArcEventsProvider,
        scheduled_events_repository: ScheduledEventsRepository,
        event_catalog_repository: EventCatalogRepository,
        map_catalog_repository: MapCatalogRepository,
    ) -> None:
        self._provider = provider
        self._scheduled_events_repository = scheduled_events_repository
        self._event_catalog_repository = event_catalog_repository
        self._map_catalog_repository = map_catalog_repository

    async def refresh_schedule(self) -> list[ScheduledEvent]:
        schedule = await self._provider.fetch_schedule()
        events_catalog = await self._event_catalog_repository.list_all()
        maps_catalog = await self._map_catalog_repository.list_all()
        event_lookup_by_external = {item.external_id: item.id for item in events_catalog if item.external_id and item.id is not None}
        event_lookup_by_canonical = {item.canonical_name: item.id for item in events_catalog if item.id is not None}
        map_lookup_by_external = {item.external_id: item.id for item in maps_catalog if item.external_id and item.id is not None}
        map_lookup_by_canonical = {item.canonical_name: item.id for item in maps_catalog if item.id is not None}
        normalized_events: list[ScheduledEvent] = []
        for item in schedule:
            event_catalog_id = self._resolve_catalog_id(
                external_id=item.event_external_id,
                canonical_name=item.event_canonical_name,
                by_external=event_lookup_by_external,
                by_canonical=event_lookup_by_canonical,
            )
            map_catalog_id = self._resolve_catalog_id(
                external_id=item.map_external_id,
                canonical_name=item.map_canonical_name,
                by_external=map_lookup_by_external,
                by_canonical=map_lookup_by_canonical,
            )
            normalized_events.append(
                ScheduledEvent(
                    id=None,
                    source_id=item.source_id,
                    event_catalog_id=event_catalog_id,
                    map_catalog_id=map_catalog_id,
                    event_display_name=item.event_display_name,
                    map_display_name=item.map_display_name,
                    starts_at=item.starts_at,
                    ends_at=item.ends_at,
                    metadata=item.metadata,
                )
            )
        return await self._scheduled_events_repository.refresh(normalized_events)

    async def list_upcoming_events(
        self,
        *,
        now: datetime | None = None,
        event_catalog_id: int | None = None,
        map_catalog_id: int | None = None,
    ) -> list[ScheduledEvent]:
        return await self._scheduled_events_repository.list_future(
            now=now or utc_now(),
            event_catalog_id=event_catalog_id,
            map_catalog_id=map_catalog_id,
        )

    async def list_events_summary(
        self,
        *,
        now: datetime | None = None,
        event_catalog_id: int | None = None,
        map_catalog_id: int | None = None,
        max_groups: int | None = EventSummaryService.DEFAULT_MAX_GROUPS,
        max_future_lines_per_group: int = EventSummaryService.DEFAULT_MAX_FUTURE_LINES_PER_GROUP,
    ) -> tuple[list[EventSummaryGroupDTO], int]:
        current_time = now or utc_now()
        scheduled_events = await self._scheduled_events_repository.list_for_summary(
            now=current_time,
            event_catalog_id=event_catalog_id,
            map_catalog_id=map_catalog_id,
        )
        known_events = await self._list_known_events_for_summary(
            event_catalog_id=event_catalog_id,
            map_catalog_id=map_catalog_id,
        )
        return EventSummaryService.build_groups(
            scheduled_events=scheduled_events,
            known_events=known_events,
            now=current_time,
            max_groups=max_groups,
            max_future_lines_per_group=max_future_lines_per_group,
        )

    async def _list_known_events_for_summary(
        self,
        *,
        event_catalog_id: int | None,
        map_catalog_id: int | None,
    ) -> list[EventDefinition]:
        if map_catalog_id is not None:
            return []
        if event_catalog_id is not None:
            event = await self._event_catalog_repository.get_by_id(event_catalog_id)
            return [event] if event is not None else []
        return await self._event_catalog_repository.list_active()

    @staticmethod
    def _resolve_catalog_id(
        *,
        external_id: str | None,
        canonical_name: str,
        by_external: dict[str, int],
        by_canonical: dict[str, int],
    ) -> int | None:
        if external_id:
            matched = by_external.get(external_id)
            if matched is not None:
                return matched
        return by_canonical.get(canonical_name)
