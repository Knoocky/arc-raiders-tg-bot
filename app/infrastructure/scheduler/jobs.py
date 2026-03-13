from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.application.services.catalog_service import CatalogService
from app.application.services.event_service import EventService
from app.application.services.notification_service import NotificationService
from app.common.config import SchedulerSettings

logger = logging.getLogger(__name__)


async def refresh_catalogs_job(catalog_service: CatalogService) -> None:
    try:
        await catalog_service.refresh_catalogs()
    except Exception:
        logger.exception("Catalog refresh job failed")


async def refresh_schedule_job(event_service: EventService) -> None:
    try:
        await event_service.refresh_schedule()
    except Exception:
        logger.exception("Schedule refresh job failed")


async def dispatch_notifications_job(notification_service: NotificationService) -> None:
    try:
        await notification_service.dispatch_due_notifications()
    except Exception:
        logger.exception("Notification dispatch job failed")


async def run_initial_sync(
    *,
    catalog_service: CatalogService,
    event_service: EventService,
    notification_service: NotificationService,
) -> None:
    logger.info("Running initial data synchronization")
    await _run_startup_step("initial catalog refresh", catalog_service.refresh_catalogs)
    await _run_startup_step("initial schedule refresh", event_service.refresh_schedule)
    await _run_startup_step("initial notification dispatch", notification_service.dispatch_due_notifications)
    logger.info("Initial data synchronization completed")


def build_scheduler(
    *,
    settings: SchedulerSettings,
    catalog_service: CatalogService,
    event_service: EventService,
    notification_service: NotificationService,
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        refresh_catalogs_job,
        trigger="interval",
        minutes=settings.catalogs_refresh_minutes,
        kwargs={"catalog_service": catalog_service},
        id="catalog_refresh",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        refresh_schedule_job,
        trigger="interval",
        minutes=settings.schedule_refresh_minutes,
        kwargs={"event_service": event_service},
        id="schedule_refresh",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        dispatch_notifications_job,
        trigger="interval",
        seconds=settings.notification_poll_seconds,
        kwargs={"notification_service": notification_service},
        id="notification_dispatch",
        max_instances=1,
        coalesce=True,
    )
    return scheduler


async def _run_startup_step(step_name: str, action) -> None:
    try:
        await action()
    except Exception:
        logger.exception("%s failed", step_name)
