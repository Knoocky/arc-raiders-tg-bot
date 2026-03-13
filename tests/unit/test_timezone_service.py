from __future__ import annotations

from datetime import UTC, datetime

import pytest


@pytest.mark.asyncio
async def test_timezone_service_returns_saved_chat_timezone(app_factory) -> None:
    app = await app_factory(None)

    context = await app.timezone_service.set_chat_timezone(chat_id=42, timezone_name="Europe/Amsterdam")
    loaded = await app.timezone_service.get_chat_timezone(chat_id=42)

    assert context.timezone_name == "Europe/Amsterdam"
    assert loaded.timezone_name == "Europe/Amsterdam"


@pytest.mark.asyncio
async def test_timezone_service_falls_back_to_utc_plus_five_when_missing(app_factory) -> None:
    app = await app_factory(None)

    context = await app.timezone_service.get_chat_timezone(chat_id=99)

    assert context.timezone_name is None
    assert context.timezone_info.tzname(None) == "UTC+5"


@pytest.mark.asyncio
async def test_timezone_service_converts_utc_datetime_to_local_time(app_factory) -> None:
    app = await app_factory(None)
    context = await app.timezone_service.set_chat_timezone(chat_id=7, timezone_name="Europe/Amsterdam")

    localized = app.timezone_service.convert_utc_to_chat_local(
        datetime(2026, 3, 11, 18, 30, tzinfo=UTC),
        timezone_context=context,
    )

    assert localized.strftime("%H:%M %Z") == "19:30 CET"


@pytest.mark.asyncio
async def test_timezone_service_formats_fallback_time(app_factory) -> None:
    app = await app_factory(None)
    context = await app.timezone_service.get_chat_timezone(chat_id=100)

    formatted = app.timezone_service.format_chat_local_time(
        datetime(2026, 3, 11, 18, 30, tzinfo=UTC),
        timezone_context=context,
    )

    assert formatted == "23:30 UTC+5"
