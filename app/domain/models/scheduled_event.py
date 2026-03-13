from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True, frozen=True)
class ScheduledEvent:
    id: int | None
    source_id: str
    event_catalog_id: int | None
    map_catalog_id: int | None
    event_display_name: str
    map_display_name: str
    starts_at: datetime
    ends_at: datetime | None = None
    metadata: dict[str, object] = field(default_factory=dict)

