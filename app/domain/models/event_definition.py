from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True, frozen=True)
class EventDefinition:
    id: int | None
    external_id: str | None
    canonical_name: str
    display_name: str
    aliases: tuple[str, ...] = field(default_factory=tuple)
    is_active: bool = True
    last_seen_at: datetime | None = None
    updated_at: datetime | None = None

