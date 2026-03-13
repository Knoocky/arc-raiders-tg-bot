from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.application.exceptions import ApplicationError, ValidationApplicationError
from app.application.services.catalog_resolver import CatalogResolver
from app.application.services.subscription_service import SubscriptionService
from app.bot.formatters.subscription_actions_formatter import format_unwatch_result
from app.bot.handlers._utils import reply_with_application_error
from app.bot.parsers.command_parser import parse_subscription_command


def register_unwatch_handlers(
    router: Router,
    *,
    catalog_resolver: CatalogResolver,
    subscription_service: SubscriptionService,
) -> None:
    @router.message(Command("unwatch"))
    async def unwatch_handler(message: Message, command: CommandObject) -> None:
        try:
            parsed = parse_subscription_command(command.args)
            if parsed.is_all:
                removed = await subscription_service.unsubscribe_all(chat_id=message.chat.id)
                await message.answer("All subscriptions removed." if removed else "No active subscriptions to remove.")
                return

            event_catalog_id = None
            map_catalog_id = None
            event_display_name = None
            map_display_name = None

            if parsed.event_name:
                event = await catalog_resolver.resolve_event_or_raise(parsed.event_name)
                if event.id is None:
                    raise ValidationApplicationError("Resolved event does not have a catalog ID.")
                event_catalog_id = event.id
                event_display_name = event.display_name

            if parsed.map_name:
                map_item = await catalog_resolver.resolve_map_or_raise(parsed.map_name)
                if map_item.id is None:
                    raise ValidationApplicationError("Resolved map does not have a catalog ID.")
                map_catalog_id = map_item.id
                map_display_name = map_item.display_name

            removed = await subscription_service.unsubscribe(
                chat_id=message.chat.id,
                event_catalog_id=event_catalog_id,
                map_catalog_id=map_catalog_id,
            )
            await message.answer(
                format_unwatch_result(
                    removed=removed,
                    event_display_name=event_display_name,
                    map_display_name=map_display_name,
                )
            )
        except ApplicationError as exc:
            await reply_with_application_error(message, exc)
