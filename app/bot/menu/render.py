from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from app.bot.menu.types import MenuScreen


async def answer_with_menu_screen(message: Message, screen: MenuScreen) -> None:
    await message.answer(
        screen.text,
        reply_markup=screen.keyboard,
        parse_mode=screen.parse_mode,
    )


async def edit_with_menu_screen(callback: CallbackQuery, screen: MenuScreen) -> None:
    if callback.message is None:
        return
    try:
        await callback.message.edit_text(
            screen.text,
            reply_markup=screen.keyboard,
            parse_mode=screen.parse_mode,
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc).casefold():
            raise


async def edit_message_with_menu_screen(
    *,
    bot: Bot,
    chat_id: int,
    message_id: int,
    screen: MenuScreen,
) -> None:
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=screen.text,
            reply_markup=screen.keyboard,
            parse_mode=screen.parse_mode,
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc).casefold():
            raise
