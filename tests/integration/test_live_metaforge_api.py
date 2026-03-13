from __future__ import annotations

import os
from typing import Any

import httpx
import pytest

from app.common.config import AppSettings
from app.infrastructure.providers.metaforge_provider import MetaForgeProvider

LIVE_API_FLAG = "RUN_LIVE_API_TESTS"

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.live_api,
]


def _is_live_api_enabled() -> bool:
    return os.environ.get(LIVE_API_FLAG, "").strip() == "1"


def _ensure_live_api_enabled() -> None:
    if not _is_live_api_enabled():
        pytest.skip(
            f"Set {LIVE_API_FLAG}=1 to run real API checks.",
        )


def _extract_items(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "items", "results", "events", "maps", "schedule"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
        return [payload] if payload else []
    return []


@pytest.mark.parametrize(
    ("path_attr", "label"),
    [
        ("schedule_path", "schedule"),
        ("events_catalog_path", "events catalog"),
    ],
)
async def test_metaforge_live_endpoints_return_200_and_data(path_attr: str, label: str) -> None:
    _ensure_live_api_enabled()
    settings = AppSettings.from_env().provider
    path = getattr(settings, path_attr)

    async with httpx.AsyncClient(base_url=settings.base_url, timeout=settings.timeout_seconds) as client:
        response = await client.get(path)

    assert response.status_code == 200, f"{label} endpoint returned {response.status_code}"
    payload = response.json()
    items = _extract_items(payload)
    assert items, f"{label} endpoint returned an empty payload"


async def test_metaforge_provider_live_requests_return_parsed_data() -> None:
    _ensure_live_api_enabled()
    settings = AppSettings.from_env().provider
    provider = MetaForgeProvider(settings)
    try:
        schedule = await provider.fetch_schedule()
        events_catalog = await provider.fetch_events_catalog()
        maps_catalog = await provider.fetch_maps_catalog()
    finally:
        await provider.aclose()

    assert schedule, "Schedule API returned no parsed events"
    assert events_catalog, "Events catalog API returned no parsed records"
    assert maps_catalog, "Maps catalog API returned no parsed records"
