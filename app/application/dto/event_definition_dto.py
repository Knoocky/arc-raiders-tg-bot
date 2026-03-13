from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.common.text_normalizer import normalize_lookup_text


class EventDefinitionDTO(BaseModel):
    external_id: str | None = None
    canonical_name: str
    display_name: str
    aliases: list[str] = Field(default_factory=list)
    is_active: bool = True

    @field_validator("canonical_name")
    @classmethod
    def validate_canonical_name(cls, value: str) -> str:
        return normalize_lookup_text(value)

