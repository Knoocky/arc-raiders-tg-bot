from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from app.application.dto.event_summary_dto import EventSummaryGroupDTO, EventSummaryLineDTO, EventSummaryLineKind
from app.domain.models.event_definition import EventDefinition
from app.domain.models.scheduled_event import ScheduledEvent


class EventSummaryService:
    DEFAULT_MAX_GROUPS: int | None = None
    DEFAULT_MAX_FUTURE_LINES_PER_GROUP = 3

    @classmethod
    def build_groups(
        cls,
        *,
        scheduled_events: list[ScheduledEvent],
        known_events: list[EventDefinition],
        now: datetime,
        max_groups: int | None = DEFAULT_MAX_GROUPS,
        max_future_lines_per_group: int = DEFAULT_MAX_FUTURE_LINES_PER_GROUP,
    ) -> tuple[list[EventSummaryGroupDTO], int]:
        grouped_events: dict[str, list[ScheduledEvent]] = defaultdict(list)
        display_names: dict[str, str] = {}
        canonical_names_by_catalog_id = {
            definition.id: definition.canonical_name
            for definition in known_events
            if definition.id is not None
        }

        for definition in known_events:
            grouped_events.setdefault(definition.canonical_name, [])
            display_names.setdefault(definition.canonical_name, definition.display_name)

        for event in scheduled_events:
            canonical_name = cls._canonical_name_for_event(
                event,
                canonical_names_by_catalog_id=canonical_names_by_catalog_id,
            )
            grouped_events[canonical_name].append(event)
            display_names.setdefault(canonical_name, event.event_display_name)

        summaries = [
            cls._build_group(
                event_canonical_name=canonical_name,
                event_display_name=display_names.get(canonical_name, canonical_name),
                events=events,
                now=now,
                max_future_lines_per_group=max_future_lines_per_group,
            )
            for canonical_name, events in grouped_events.items()
        ]
        summaries.sort(key=lambda group: cls._sort_key(group))

        if max_groups is None:
            return summaries, 0

        hidden_groups = max(len(summaries) - max_groups, 0)
        return summaries[:max_groups], hidden_groups

    @classmethod
    def _build_group(
        cls,
        *,
        event_canonical_name: str,
        event_display_name: str,
        events: list[ScheduledEvent],
        now: datetime,
        max_future_lines_per_group: int,
    ) -> EventSummaryGroupDTO:
        active_events = [
            event
            for event in events
            if event.ends_at is not None and event.starts_at <= now < event.ends_at
        ]
        future_events = sorted((event for event in events if event.starts_at > now), key=lambda item: item.starts_at)

        if active_events:
            primary_event = min(active_events, key=lambda item: item.ends_at or item.starts_at)
            primary_line = cls._to_line(primary_event, kind=EventSummaryLineKind.ACTIVE)
        elif future_events:
            primary_event = future_events[0]
            primary_line = cls._to_line(primary_event, kind=EventSummaryLineKind.FUTURE)
            future_events = future_events[1:]
        else:
            primary_line = None
            future_events = []

        future_lines = tuple(
            cls._to_line(event, kind=EventSummaryLineKind.FUTURE)
            for event in future_events[: max(max_future_lines_per_group, 0)]
        )
        return EventSummaryGroupDTO(
            event_canonical_name=event_canonical_name,
            event_display_name=event_display_name,
            primary_line=primary_line,
            future_lines=future_lines,
        )

    @staticmethod
    def _canonical_name_for_event(
        event: ScheduledEvent,
        *,
        canonical_names_by_catalog_id: dict[int, str],
    ) -> str:
        if event.event_catalog_id is not None:
            matched = canonical_names_by_catalog_id.get(event.event_catalog_id)
            if matched is not None:
                return matched
        metadata_name = event.metadata.get("event_canonical_name")
        if isinstance(metadata_name, str) and metadata_name.strip():
            return metadata_name.strip()
        return event.event_display_name.casefold()

    @staticmethod
    def _to_line(event: ScheduledEvent, *, kind: EventSummaryLineKind) -> EventSummaryLineDTO:
        return EventSummaryLineDTO(
            map_display_name=event.map_display_name,
            starts_at=event.starts_at,
            ends_at=event.ends_at,
            kind=kind,
        )

    @staticmethod
    def _sort_key(group: EventSummaryGroupDTO) -> tuple[int, datetime | None, str]:
        if group.primary_line is None:
            return (1, None, group.event_display_name.casefold())
        return (0, group.primary_line.starts_at, group.event_display_name.casefold())
