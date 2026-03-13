from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.formatters.help_formatter import build_help_text


def register_help_handlers(router: Router) -> None:
    @router.message(Command("help"))
    async def help_handler(message: Message) -> None:
        await message.answer(build_help_text(), parse_mode=None)
