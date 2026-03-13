from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.application.dto.map_definition_dto import MapDefinitionDTO


@dataclass(frozen=True, slots=True)
class MapCatalogSeed:
    display_name: str
    aliases: tuple[str, ...] = ()


# MetaForge does not expose a documented `/api/arc-raiders/maps` endpoint.
# Until an official list endpoint exists, the adapter keeps a fallback catalog
# inside the provider layer so application services stay source-agnostic.
FALLBACK_MAP_CATALOG: tuple[MapCatalogSeed, ...] = (
    MapCatalogSeed(display_name="Dam"),
    MapCatalogSeed(display_name="Spaceport", aliases=("Space port",)),
    MapCatalogSeed(display_name="Buried City"),
    MapCatalogSeed(display_name="Blue Gate", aliases=("Blue gate",)),
    MapCatalogSeed(display_name="Stella Montis"),
)


def build_fallback_maps_catalog() -> list[MapDefinitionDTO]:
    return [
        MapDefinitionDTO(
            display_name=seed.display_name,
            canonical_name=seed.display_name,
            aliases=list(seed.aliases),
        )
        for seed in FALLBACK_MAP_CATALOG
    ]


def merge_map_catalogs(
    *,
    primary: Iterable[MapDefinitionDTO],
    fallback: Iterable[MapDefinitionDTO],
) -> list[MapDefinitionDTO]:
    merged_by_canonical: dict[str, MapDefinitionDTO] = {}

    for item in fallback:
        merged_by_canonical[item.canonical_name] = item

    for item in primary:
        existing = merged_by_canonical.get(item.canonical_name)
        if existing is None:
            merged_by_canonical[item.canonical_name] = item
            continue

        aliases = list(dict.fromkeys([*existing.aliases, *item.aliases]))
        merged_by_canonical[item.canonical_name] = item.model_copy(update={"aliases": aliases})

    return sorted(merged_by_canonical.values(), key=lambda item: item.display_name)
