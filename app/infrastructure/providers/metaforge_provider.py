from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from app.application.dto.event_definition_dto import EventDefinitionDTO
from app.application.dto.map_definition_dto import MapDefinitionDTO
from app.application.dto.scheduled_event_dto import ScheduledEventDTO
from app.application.exceptions import ProviderApplicationError
from app.common.config import ProviderSettings
from app.common.text_normalizer import normalize_lookup_text
from app.infrastructure.providers.map_catalog_source import build_fallback_maps_catalog, merge_map_catalogs

logger = logging.getLogger(__name__)


class MetaForgeProvider:
    def __init__(
        self,
        settings: ProviderSettings,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings
        self._client = client or httpx.AsyncClient(
            base_url=settings.base_url,
            timeout=settings.timeout_seconds,
        )
        self._owns_client = client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def fetch_schedule(self) -> list[ScheduledEventDTO]:
        payload = await self._fetch_json(self._settings.schedule_path)
        items = self._extract_items(payload)
        schedule: list[ScheduledEventDTO] = []
        for item in items:
            if not isinstance(item, dict):
                logger.warning("Skipping non-object schedule item: %r", item)
                continue
            try:
                schedule.append(self._parse_schedule_item(item))
            except ProviderApplicationError as exc:
                logger.warning("Skipping malformed schedule item: %s", exc)
        return schedule

    async def fetch_events_catalog(self) -> list[EventDefinitionDTO]:
        catalog = await self._fetch_catalog(
            self._settings.events_catalog_path,
            parser=self._parse_event_definition,
        )
        if catalog:
            return catalog

        logger.warning("Falling back to schedule-derived events catalog")
        schedule = await self.fetch_schedule()
        deduped: dict[str, EventDefinitionDTO] = {}
        for item in schedule:
            deduped.setdefault(
                item.event_canonical_name,
                EventDefinitionDTO(
                    external_id=item.event_external_id,
                    canonical_name=item.event_canonical_name,
                    display_name=item.event_display_name,
                ),
            )
        return list(deduped.values())

    async def fetch_maps_catalog(self) -> list[MapDefinitionDTO]:
        # `/api/arc-raiders/maps` does not exist. We derive maps from
        # documented schedule data and then merge a local fallback catalog
        # until MetaForge exposes an official maps list endpoint.
        derived_catalog = await self._fetch_maps_catalog_from_documented_sources()
        return merge_map_catalogs(
            primary=derived_catalog,
            fallback=build_fallback_maps_catalog(),
        )

    async def _fetch_catalog(self, path: str, *, parser: Any) -> list[Any]:
        try:
            payload = await self._fetch_json(path)
        except ProviderApplicationError as exc:
            logger.warning("Catalog fetch failed for %s: %s", path, exc)
            return []

        catalog: list[Any] = []
        for item in self._extract_items(payload):
            if not isinstance(item, dict):
                logger.warning("Skipping non-object catalog item: %r", item)
                continue
            try:
                catalog.append(parser(item))
            except ProviderApplicationError as exc:
                logger.warning("Skipping malformed catalog item: %s", exc)
        return catalog

    async def _fetch_json(self, path: str) -> Any:
        try:
            response = await self._client.get(path)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderApplicationError(f"Provider request failed for {path}: {exc}") from exc

        try:
            return response.json()
        except ValueError as exc:
            raise ProviderApplicationError(f"Provider returned non-JSON payload for {path}") from exc

    @staticmethod
    def _extract_items(payload: Any) -> list[Any]:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("data", "items", "results", "events", "maps", "schedule"):
                value = payload.get(key)
                if isinstance(value, list):
                    return value
            if payload:
                return [payload]
        return []

    def _parse_event_definition(self, item: dict[str, Any]) -> EventDefinitionDTO:
        display_name = self._pick_string(
            item,
            "display_name",
            "displayName",
            "name",
            "title",
            "label",
        )
        if display_name is None:
            raise ProviderApplicationError("Missing event display name")

        canonical_name = self._pick_string(item, "canonical_name", "canonicalName", "slug") or display_name
        aliases = self._pick_aliases(item)
        return EventDefinitionDTO(
            external_id=self._pick_string(item, "external_id", "externalId", "id"),
            canonical_name=canonical_name,
            display_name=display_name,
            aliases=aliases,
            is_active=bool(item.get("is_active", item.get("isActive", True))),
        )

    def _parse_map_definition(self, item: dict[str, Any]) -> MapDefinitionDTO:
        display_name = self._pick_string(
            item,
            "display_name",
            "displayName",
            "name",
            "title",
            "label",
        )
        if display_name is None:
            raise ProviderApplicationError("Missing map display name")

        canonical_name = self._pick_string(item, "canonical_name", "canonicalName", "slug") or display_name
        aliases = self._pick_aliases(item)
        return MapDefinitionDTO(
            external_id=self._pick_string(item, "external_id", "externalId", "id"),
            canonical_name=canonical_name,
            display_name=display_name,
            aliases=aliases,
            is_active=bool(item.get("is_active", item.get("isActive", True))),
        )

    async def _fetch_maps_catalog_from_documented_sources(self) -> list[MapDefinitionDTO]:
        try:
            schedule = await self.fetch_schedule()
        except ProviderApplicationError as exc:
            logger.warning("Map catalog derivation from schedule failed: %s", exc)
            return []

        deduped: dict[str, MapDefinitionDTO] = {}
        for item in schedule:
            deduped.setdefault(
                item.map_canonical_name,
                MapDefinitionDTO(
                    external_id=item.map_external_id,
                    canonical_name=item.map_canonical_name,
                    display_name=item.map_display_name,
                ),
            )
        return list(deduped.values())

    def _parse_schedule_item(self, item: dict[str, Any]) -> ScheduledEventDTO:
        event_node = item.get("event") if isinstance(item.get("event"), dict) else {}
        map_node = item.get("map") if isinstance(item.get("map"), dict) else {}
        raw_map_name = item.get("map") if isinstance(item.get("map"), str) else None

        source_id = self._pick_string(item, "source_id", "sourceId", "id", "uuid")
        starts_at_raw = self._pick_datetime_raw(
            item,
            "starts_at",
            "startsAt",
            "start_at",
            "startAt",
            "start_time",
            "startTime",
            "start",
        )
        if starts_at_raw is None:
            raise ProviderApplicationError("Missing scheduled event start time")

        event_display_name = self._pick_string(
            event_node,
            "display_name",
            "displayName",
            "name",
            "title",
        ) or self._pick_string(
            item,
            "event_display_name",
            "eventDisplayName",
            "event_name",
            "eventName",
            "name",
        )
        map_display_name = self._pick_string(
            map_node,
            "display_name",
            "displayName",
            "name",
            "title",
        ) or self._pick_string(
            item,
            "map_display_name",
            "mapDisplayName",
            "map_name",
            "mapName",
        ) or raw_map_name

        if event_display_name is None or map_display_name is None:
            raise ProviderApplicationError("Missing event or map display name in schedule item")

        if source_id is None:
            source_id = self._build_schedule_source_id(
                event_display_name=event_display_name,
                map_display_name=map_display_name,
                starts_at_raw=starts_at_raw,
            )

        event_canonical_name = self._pick_string(
            event_node,
            "canonical_name",
            "canonicalName",
            "slug",
        ) or self._pick_string(item, "event_canonical_name", "eventCanonicalName") or event_display_name
        map_canonical_name = self._pick_string(
            map_node,
            "canonical_name",
            "canonicalName",
            "slug",
        ) or self._pick_string(item, "map_canonical_name", "mapCanonicalName") or map_display_name

        ends_at_raw = self._pick_datetime_raw(
            item,
            "ends_at",
            "endsAt",
            "end_at",
            "endAt",
            "end_time",
            "endTime",
            "end",
        )

        return ScheduledEventDTO(
            source_id=source_id,
            event_external_id=self._pick_string(
                event_node,
                "external_id",
                "externalId",
                "id",
            ) or self._pick_string(item, "event_external_id", "eventExternalId", "event_id", "eventId"),
            event_canonical_name=event_canonical_name,
            event_display_name=event_display_name,
            map_external_id=self._pick_string(
                map_node,
                "external_id",
                "externalId",
                "id",
            ) or self._pick_string(item, "map_external_id", "mapExternalId", "map_id", "mapId"),
            map_canonical_name=map_canonical_name,
            map_display_name=map_display_name,
            starts_at=self._parse_datetime(starts_at_raw),
            ends_at=self._parse_datetime(ends_at_raw) if ends_at_raw else None,
            metadata=item,
        )

    @staticmethod
    def _pick_string(container: dict[str, Any], *keys: str) -> str | None:
        for key in keys:
            value = container.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    @staticmethod
    def _pick_datetime_raw(container: dict[str, Any], *keys: str) -> str | int | float | None:
        for key in keys:
            value = container.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
            if isinstance(value, (int, float)):
                return value
        return None

    @staticmethod
    def _pick_aliases(container: dict[str, Any]) -> list[str]:
        aliases: list[str] = []
        for key in ("aliases", "alias", "synonyms"):
            value = container.get(key)
            if isinstance(value, list):
                aliases.extend(alias.strip() for alias in value if isinstance(alias, str) and alias.strip())
            elif isinstance(value, str) and value.strip():
                aliases.append(value.strip())

        deduped: dict[str, str] = {}
        for alias in aliases:
            deduped.setdefault(normalize_lookup_text(alias), alias)
        return list(deduped.values())

    @staticmethod
    def _parse_datetime(value: str | int | float) -> datetime:
        if isinstance(value, (int, float)):
            timestamp = float(value)
            if timestamp > 10_000_000_000:
                timestamp /= 1000.0
            return datetime.fromtimestamp(timestamp, tz=UTC)

        normalized_value = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized_value)
        except ValueError as exc:
            raise ProviderApplicationError(f"Invalid datetime value: {value}") from exc
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    @staticmethod
    def _build_schedule_source_id(
        *,
        event_display_name: str,
        map_display_name: str,
        starts_at_raw: str | int | float,
    ) -> str:
        return "|".join(
            [
                normalize_lookup_text(event_display_name),
                normalize_lookup_text(map_display_name),
                str(starts_at_raw).strip(),
            ]
        )
