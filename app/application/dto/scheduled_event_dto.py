from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.common.text_normalizer import normalize_lookup_text
from app.common.time_utils import ensure_utc


class ScheduledEventDTO(BaseModel):
    source_id: str
    event_external_id: str | None = None
    event_canonical_name: str
    event_display_name: str
    map_external_id: str | None = None
    map_canonical_name: str
    map_display_name: str
    starts_at: datetime
    ends_at: datetime | None = None
    metadata: dict[str, object] = Field(default_factory=dict)

    @field_validator("event_canonical_name", "map_canonical_name")
    @classmethod
    def validate_canonical_names(cls, value: str) -> str:
        return normalize_lookup_text(value)

    @field_validator("starts_at", "ends_at")
    @classmethod
    def validate_datetimes(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_utc(value)

