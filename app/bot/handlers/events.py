from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.application.exceptions import ApplicationError, ValidationApplicationError
from app.application.services.catalog_resolver import CatalogResolver
from app.application.services.event_service import EventService
from app.application.services.timezone_service import TimezoneService
from app.bot.handlers._utils import reply_with_application_error
from app.bot.parsers.command_parser import parse_events_command
from app.bot.presenters.events_presenter import build_events_summary_text


def register_events_handlers(
    router: Router,
    *,
    event_service: EventService,
    catalog_resolver: CatalogResolver,
    timezone_service: TimezoneService,
) -> None:
    @router.message(Command("events"))
    async def events_handler(message: Message, command: CommandObject) -> None:
        try:
            parsed = parse_events_command(command.args)
            event_catalog_id = None
            map_catalog_id = None
            if parsed.event_name:
                event = await catalog_resolver.resolve_event_or_raise(parsed.event_name)
                if event.id is None:
                    raise ValidationApplicationError("Resolved event does not have a catalog ID.")
                event_catalog_id = event.id
            if parsed.map_name:
                map_item = await catalog_resolver.resolve_map_or_raise(parsed.map_name)
                if map_item.id is None:
                    raise ValidationApplicationError("Resolved map does not have a catalog ID.")
                map_catalog_id = map_item.id

            text = await build_events_summary_text(
                chat_id=message.chat.id,
                event_service=event_service,
                timezone_service=timezone_service,
                event_catalog_id=event_catalog_id,
                map_catalog_id=map_catalog_id,
                max_future_lines_per_group=_full_schedule_future_lines_limit(
                    event_catalog_id=event_catalog_id,
                    map_catalog_id=map_catalog_id,
                ),
            )
            await message.answer(text)
        except ApplicationError as exc:
            await reply_with_application_error(message, exc)


def _full_schedule_future_lines_limit(
    *,
    event_catalog_id: int | None,
    map_catalog_id: int | None,
) -> int | None:
    if event_catalog_id is None and map_catalog_id is None:
        return 1
    return None
