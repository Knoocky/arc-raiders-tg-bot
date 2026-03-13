from __future__ import annotations

from difflib import get_close_matches
from typing import TypeVar

from app.application.exceptions import EntityNotFoundError
from app.common.text_normalizer import normalize_lookup_text
from app.domain.models.event_definition import EventDefinition
from app.domain.models.map_definition import MapDefinition
from app.infrastructure.persistence.repositories.event_catalog_repository import EventCatalogRepository
from app.infrastructure.persistence.repositories.map_catalog_repository import MapCatalogRepository

CatalogItem = TypeVar("CatalogItem", EventDefinition, MapDefinition)


class CatalogResolver:
    def __init__(
        self,
        *,
        event_catalog_repository: EventCatalogRepository,
        map_catalog_repository: MapCatalogRepository,
    ) -> None:
        self._event_catalog_repository = event_catalog_repository
        self._map_catalog_repository = map_catalog_repository

    async def resolve_event(self, user_input: str) -> EventDefinition | None:
        return self._resolve(user_input, await self._event_catalog_repository.list_active())

    async def resolve_map(self, user_input: str) -> MapDefinition | None:
        return self._resolve(user_input, await self._map_catalog_repository.list_active())

    async def resolve_event_or_raise(self, user_input: str) -> EventDefinition:
        catalog = await self._event_catalog_repository.list_active()
        match = self._resolve(user_input, catalog)
        if match is None:
            raise EntityNotFoundError("event", user_input, self._suggest(user_input, catalog))
        return match

    async def resolve_map_or_raise(self, user_input: str) -> MapDefinition:
        catalog = await self._map_catalog_repository.list_active()
        match = self._resolve(user_input, catalog)
        if match is None:
            raise EntityNotFoundError("map", user_input, self._suggest(user_input, catalog))
        return match

    async def suggest_events(self, user_input: str) -> list[str]:
        return self._suggest(user_input, await self._event_catalog_repository.list_active())

    async def suggest_maps(self, user_input: str) -> list[str]:
        return self._suggest(user_input, await self._map_catalog_repository.list_active())

    def _resolve(self, user_input: str, catalog: list[CatalogItem]) -> CatalogItem | None:
        lookup = normalize_lookup_text(user_input)
        if not lookup:
            return None

        for item in catalog:
            if lookup in self._build_lookup_candidates(item):
                return item
        return None

    def _suggest(self, user_input: str, catalog: list[CatalogItem]) -> list[str]:
        lookup = normalize_lookup_text(user_input)
        display_by_lookup: dict[str, str] = {}
        for item in catalog:
            for candidate in self._build_lookup_candidates(item):
                display_by_lookup.setdefault(candidate, item.display_name)

        suggestions = get_close_matches(lookup, list(display_by_lookup), n=3, cutoff=0.6)
        deduped: list[str] = []
        for suggestion in suggestions:
            display_name = display_by_lookup[suggestion]
            if display_name not in deduped:
                deduped.append(display_name)
        return deduped

    @staticmethod
    def _build_lookup_candidates(item: CatalogItem) -> set[str]:
        candidates = {
            item.canonical_name,
            normalize_lookup_text(item.display_name),
        }
        candidates.update(normalize_lookup_text(alias) for alias in item.aliases)
        return {candidate for candidate in candidates if candidate}
