from __future__ import annotations

from aiogram import Router

from app.application.services.catalog_resolver import CatalogResolver
from app.application.services.catalog_service import CatalogService
from app.application.services.event_service import EventService
from app.application.services.notification_service import NotificationService
from app.application.services.subscription_service import SubscriptionService
from app.application.services.timezone_service import TimezoneService
from app.bot.handlers.catalog import register_catalog_handlers
from app.bot.handlers.events import register_events_handlers
from app.bot.handlers.help import register_help_handlers
from app.bot.handlers.list_subscriptions import register_list_handlers
from app.bot.handlers.menu import register_menu_handlers
from app.bot.handlers.notify import register_notify_handlers
from app.bot.handlers.unwatch import register_unwatch_handlers
from app.bot.handlers.watch import register_watch_handlers
from app.bot.menu.controller import MenuController


def create_bot_router(
    *,
    catalog_service: CatalogService,
    catalog_resolver: CatalogResolver,
    event_service: EventService,
    subscription_service: SubscriptionService,
    notification_service: NotificationService,
    timezone_service: TimezoneService,
) -> Router:
    router = Router()
    menu_controller = MenuController(
        catalog_service=catalog_service,
        event_service=event_service,
        subscription_service=subscription_service,
        notification_service=notification_service,
        timezone_service=timezone_service,
    )
    register_menu_handlers(router, menu_controller=menu_controller)
    register_help_handlers(router)
    register_events_handlers(
        router,
        event_service=event_service,
        catalog_resolver=catalog_resolver,
        timezone_service=timezone_service,
    )
    register_watch_handlers(
        router,
        catalog_resolver=catalog_resolver,
        subscription_service=subscription_service,
    )
    register_unwatch_handlers(
        router,
        catalog_resolver=catalog_resolver,
        subscription_service=subscription_service,
    )
    register_notify_handlers(router, notification_service=notification_service)
    register_list_handlers(
        router,
        subscription_service=subscription_service,
        notification_service=notification_service,
    )
    register_catalog_handlers(router, catalog_service=catalog_service)
    return router
