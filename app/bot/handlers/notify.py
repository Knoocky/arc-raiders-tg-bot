from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.application.exceptions import ApplicationError
from app.application.services.notification_service import NotificationService
from app.bot.formatters.notifications_formatter import format_offsets
from app.bot.handlers._utils import reply_with_application_error
from app.bot.parsers.command_parser import parse_notify_command


def register_notify_handlers(
    router: Router,
    *,
    notification_service: NotificationService,
) -> None:
    @router.message(Command("notify"))
    async def notify_handler(message: Message, command: CommandObject) -> None:
        try:
            parsed = parse_notify_command(command.args)
            if parsed.action == "list":
                offsets = await notification_service.list_offsets(chat_id=message.chat.id)
                await message.answer(format_offsets(offsets))
                return
            if parsed.action == "replace":
                offsets = await notification_service.replace_offsets(chat_id=message.chat.id, minutes=parsed.minutes)
                await message.answer("Notification offsets replaced.\n" + format_offsets(offsets))
                return
            if parsed.action == "add":
                offsets = await notification_service.add_offsets(chat_id=message.chat.id, minutes=parsed.minutes)
                await message.answer("Notification offsets updated.\n" + format_offsets(offsets))
                return

            offsets = await notification_service.remove_offsets(chat_id=message.chat.id, minutes=parsed.minutes)
            await message.answer("Notification offsets updated.\n" + format_offsets(offsets))
        except ApplicationError as exc:
            await reply_with_application_error(message, exc)

