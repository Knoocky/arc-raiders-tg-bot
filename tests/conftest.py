from __future__ import annotations

from dataclasses import dataclass

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.application.services.catalog_resolver import CatalogResolver
from app.application.services.catalog_service import CatalogService
from app.application.services.event_service import EventService
from app.application.services.notification_service import NotificationService
from app.application.services.subscription_service import SubscriptionService
from app.application.services.timezone_service import TimezoneService
from app.bot.formatters.notifications_formatter import format_notification_message
from app.bot.menu.controller import MenuController
from app.infrastructure.persistence.models import Base
from app.infrastructure.persistence.repositories.chat_timezone_settings_repository import ChatTimezoneSettingsRepository
from app.infrastructure.persistence.repositories.event_catalog_repository import EventCatalogRepository
from app.infrastructure.persistence.repositories.map_catalog_repository import MapCatalogRepository
from app.infrastructure.persistence.repositories.notification_log_repository import NotificationLogRepository
from app.infrastructure.persistence.repositories.notification_settings_repository import NotificationSettingsRepository
from app.infrastructure.persistence.repositories.scheduled_events_repository import ScheduledEventsRepository
from app.infrastructure.persistence.repositories.subscriptions_repository import SubscriptionsRepository


class RecordingSender:
    def __init__(self) -> None:
        self.messages: list[tuple[int, str]] = []

    async def send_message(self, chat_id: int, text: str) -> None:
        self.messages.append((chat_id, text))


@dataclass(slots=True)
class TestApp:
    sender: RecordingSender
    catalog_service: CatalogService
    catalog_resolver: CatalogResolver
    event_service: EventService
    subscription_service: SubscriptionService
    notification_service: NotificationService
    timezone_service: TimezoneService
    menu_controller: MenuController


@pytest_asyncio.fixture
async def app_factory():
    engines = []

    async def _factory(provider) -> TestApp:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
        engines.append(engine)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
        event_catalog_repository = EventCatalogRepository(session_factory)
        map_catalog_repository = MapCatalogRepository(session_factory)
        scheduled_events_repository = ScheduledEventsRepository(session_factory)
        subscriptions_repository = SubscriptionsRepository(session_factory)
        chat_timezone_settings_repository = ChatTimezoneSettingsRepository(session_factory)
        notification_settings_repository = NotificationSettingsRepository(session_factory)
        notification_log_repository = NotificationLogRepository(session_factory)

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
        sender = RecordingSender()
        notification_service = NotificationService(
            event_service=event_service,
            subscription_service=subscription_service,
            timezone_service=timezone_service,
            notification_settings_repository=notification_settings_repository,
            notification_log_repository=notification_log_repository,
            sender=sender,
            message_formatter=format_notification_message,
        )
        menu_controller = MenuController(
            catalog_service=catalog_service,
            event_service=event_service,
            subscription_service=subscription_service,
            notification_service=notification_service,
            timezone_service=timezone_service,
        )
        return TestApp(
            sender=sender,
            catalog_service=catalog_service,
            catalog_resolver=catalog_resolver,
            event_service=event_service,
            subscription_service=subscription_service,
            notification_service=notification_service,
            timezone_service=timezone_service,
            menu_controller=menu_controller,
        )

    yield _factory

    for engine in engines:
        await engine.dispose()
