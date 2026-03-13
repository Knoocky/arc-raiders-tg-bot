from __future__ import annotations

from aiogram.types import Message

from app.application.exceptions import ApplicationError
from app.bot.formatters.error_formatter import format_error_message


async def reply_with_application_error(message: Message, error: ApplicationError) -> None:
    await message.answer(format_error_message(str(error)))

