import pytest

from app.infrastructure.scheduler.jobs import run_initial_sync


class RecordingCatalogService:
    def __init__(self, calls: list[str]) -> None:
        self._calls = calls

    async def refresh_catalogs(self) -> None:
        self._calls.append("catalogs")


class RecordingEventService:
    def __init__(self, calls: list[str], *, should_fail: bool = False) -> None:
        self._calls = calls
        self._should_fail = should_fail

    async def refresh_schedule(self) -> None:
        self._calls.append("schedule")
        if self._should_fail:
            raise RuntimeError("schedule failed")


class RecordingNotificationService:
    def __init__(self, calls: list[str]) -> None:
        self._calls = calls

    async def dispatch_due_notifications(self) -> int:
        self._calls.append("notifications")
        return 0


@pytest.mark.asyncio
async def test_run_initial_sync_calls_all_steps_in_order() -> None:
    calls: list[str] = []

    await run_initial_sync(
        catalog_service=RecordingCatalogService(calls),
        event_service=RecordingEventService(calls),
        notification_service=RecordingNotificationService(calls),
    )

    assert calls == ["catalogs", "schedule", "notifications"]


@pytest.mark.asyncio
async def test_run_initial_sync_continues_when_one_step_fails() -> None:
    calls: list[str] = []

    await run_initial_sync(
        catalog_service=RecordingCatalogService(calls),
        event_service=RecordingEventService(calls, should_fail=True),
        notification_service=RecordingNotificationService(calls),
    )

    assert calls == ["catalogs", "schedule", "notifications"]
