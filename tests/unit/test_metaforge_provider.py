from __future__ import annotations

import httpx
import pytest

from app.common.config import ProviderSettings
from app.infrastructure.providers.map_catalog_source import build_fallback_maps_catalog
from app.infrastructure.providers.metaforge_provider import MetaForgeProvider


@pytest.mark.asyncio
async def test_metaforge_provider_parses_schedule_and_skips_malformed_items() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/events-schedule"
        return httpx.Response(
            200,
            json=[
                {
                    "id": "1",
                    "event_name": "Meteor Shower",
                    "map_name": "Blue Gate",
                    "starts_at": "2026-03-11T18:30:00Z",
                },
                {
                    "id": "bad",
                    "event_name": "Broken",
                },
            ],
        )

    client = httpx.AsyncClient(
        base_url="https://example.test",
        transport=httpx.MockTransport(handler),
    )
    provider = MetaForgeProvider(ProviderSettings(base_url="https://example.test"), client=client)

    schedule = await provider.fetch_schedule()

    assert len(schedule) == 1
    assert schedule[0].event_display_name == "Meteor Shower"
    assert schedule[0].map_display_name == "Blue Gate"
    await client.aclose()


@pytest.mark.asyncio
async def test_metaforge_provider_parses_current_live_schedule_shape() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/events-schedule"
        return httpx.Response(
            200,
            json={
                "cachedAt": "2026-03-11T12:00:00Z",
                "data": [
                    {
                        "name": "Meteor Shower",
                        "map": "Blue Gate",
                        "startTime": 1773253800000,
                        "endTime": 1773255600000,
                        "icon": "https://example.test/icon.png",
                    }
                ],
            },
        )

    client = httpx.AsyncClient(
        base_url="https://example.test",
        transport=httpx.MockTransport(handler),
    )
    provider = MetaForgeProvider(ProviderSettings(base_url="https://example.test"), client=client)

    schedule = await provider.fetch_schedule()

    assert len(schedule) == 1
    assert schedule[0].source_id == "meteor shower|blue gate|1773253800000"
    assert schedule[0].event_display_name == "Meteor Shower"
    assert schedule[0].map_display_name == "Blue Gate"
    assert schedule[0].starts_at.isoformat() == "2026-03-11T18:30:00+00:00"
    await client.aclose()


@pytest.mark.asyncio
async def test_metaforge_provider_derives_maps_from_schedule_and_merges_fallback_catalog() -> None:
    requested_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_paths.append(request.url.path)
        if request.url.path == "/events":
            return httpx.Response(404, json={"detail": "not found"})
        return httpx.Response(
            200,
            json=[
                {
                    "id": "1",
                    "event_name": "Meteor Shower",
                    "map_name": "Frontier Basin",
                    "starts_at": "2026-03-11T18:30:00Z",
                }
            ],
        )

    client = httpx.AsyncClient(
        base_url="https://example.test",
        transport=httpx.MockTransport(handler),
    )
    provider = MetaForgeProvider(ProviderSettings(base_url="https://example.test"), client=client)

    events_catalog = await provider.fetch_events_catalog()
    maps_catalog = await provider.fetch_maps_catalog()

    assert events_catalog[0].display_name == "Meteor Shower"
    assert requested_paths == ["/events", "/events-schedule", "/events-schedule"]
    assert "/maps" not in requested_paths
    assert {item.display_name for item in maps_catalog} >= {
        "Dam",
        "Spaceport",
        "Buried City",
        "Blue Gate",
        "Stella Montis",
        "Frontier Basin",
    }
    await client.aclose()


def test_fallback_maps_catalog_builds_normalized_dtos() -> None:
    catalog = build_fallback_maps_catalog()

    assert [item.display_name for item in catalog] == [
        "Dam",
        "Spaceport",
        "Buried City",
        "Blue Gate",
        "Stella Montis",
    ]
    assert [item.canonical_name for item in catalog] == [
        "dam",
        "spaceport",
        "buried city",
        "blue gate",
        "stella montis",
    ]
    assert catalog[1].aliases == ["Space port"]
    assert catalog[3].aliases == ["Blue gate"]
