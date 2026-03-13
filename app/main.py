from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.application.services.catalog_resolver import CatalogResolver
from app.application.services.catalog_service import CatalogService
from app.application.services.event_service import EventService
from app.application.services.notification_service import NotificationService
from app.application.services.subscription_service import SubscriptionService
from app.application.services.timezone_service import TimezoneService
from app.bot.formatters.notifications_formatter import format_notification_message
from app.bot.router import create_bot_router
from app.bot.sender import AiogramNotificationSender
from app.common.config import AppSettings
from app.common.logging import configure_logging
from app.infrastructure.persistence.db import create_engine
from app.infrastructure.persistence.repositories.event_catalog_repository import EventCatalogRepository
from app.infrastructure.persistence.repositories.map_catalog_repository import MapCatalogRepository
from app.infrastructure.persistence.repositories.chat_timezone_settings_repository import ChatTimezoneSettingsRepository
from app.infrastructure.persistence.repositories.notification_log_repository import NotificationLogRepository
from app.infrastructure.persistence.repositories.notification_settings_repository import NotificationSettingsRepository
from app.infrastructure.persistence.repositories.scheduled_events_repository import ScheduledEventsRepository
from app.infrastructure.persistence.repositories.subscriptions_repository import SubscriptionsRepository
from app.infrastructure.providers.metaforge_provider import MetaForgeProvider
from app.infrastructure.scheduler.jobs import (
    build_scheduler,
    run_initial_sync,
)

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = AppSettings.from_env()
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is required.")

    configure_logging(settings.log_level)
    engine = create_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

    event_catalog_repository = EventCatalogRepository(session_factory)
    map_catalog_repository = MapCatalogRepository(session_factory)
    scheduled_events_repository = ScheduledEventsRepository(session_factory)
    subscriptions_repository = SubscriptionsRepository(session_factory)
    chat_timezone_settings_repository = ChatTimezoneSettingsRepository(session_factory)
    notification_settings_repository = NotificationSettingsRepository(session_factory)
    notification_log_repository = NotificationLogRepository(session_factory)

    provider = MetaForgeProvider(settings.provider)

    catalog_service = CatalogService(
        provider=provider,
        event_catalog_repository=event_catalog_repository,
        map_catalog_repository=map_catalog_repository,
    )
    catalog_resolver = CatalogResolver(
        event_catalog_repository=event_catalog_repository,
        map_catalog_repository=map_catalog_repository,
    )
    event_service = EventService(
        provider=provider,
        scheduled_events_repository=scheduled_events_repository,
        event_catalog_repository=event_catalog_repository,
        map_catalog_repository=map_catalog_repository,
    )
    subscription_service = SubscriptionService(
        subscriptions_repository=subscriptions_repository,
        event_catalog_repository=event_catalog_repository,
        map_catalog_repository=map_catalog_repository,
    )
    timezone_service = TimezoneService(chat_timezone_settings_repository)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    sender = AiogramNotificationSender(bot)
    notification_service = NotificationService(
        event_service=event_service,
        subscription_service=subscription_service,
        timezone_service=timezone_service,
        notification_settings_repository=notification_settings_repository,
        notification_log_repository=notification_log_repository,
        sender=sender,
        message_formatter=format_notification_message,
    )

    router = create_bot_router(
        catalog_service=catalog_service,
        catalog_resolver=catalog_resolver,
        event_service=event_service,
        subscription_service=subscription_service,
        notification_service=notification_service,
        timezone_service=timezone_service,
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    scheduler = build_scheduler(
        settings=settings.scheduler,
        catalog_service=catalog_service,
        event_service=event_service,
        notification_service=notification_service,
    )

    await run_initial_sync(
        catalog_service=catalog_service,
        event_service=event_service,
        notification_service=notification_service,
    )

    scheduler.start()
    try:
        await dispatcher.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await provider.aclose()
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
