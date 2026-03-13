from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EventSummaryLineKind(str, Enum):
    ACTIVE = "active"
    FUTURE = "future"


@dataclass(slots=True, frozen=True)
class EventSummaryLineDTO:
    map_display_name: str
    starts_at: datetime
    ends_at: datetime | None
    kind: EventSummaryLineKind


@dataclass(slots=True, frozen=True)
class EventSummaryGroupDTO:
    event_canonical_name: str
    event_display_name: str
    primary_line: EventSummaryLineDTO | None
    future_lines: tuple[EventSummaryLineDTO, ...] = field(default_factory=tuple)

    @property
    def has_scheduled_events(self) -> bool:
        return self.primary_line is not None
