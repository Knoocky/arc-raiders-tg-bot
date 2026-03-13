from __future__ import annotations

from collections.abc import Sequence

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_menu_keyboard(
    *,
    item_rows: Sequence[Sequence[InlineKeyboardButton]],
    back_callback_data: str | None = None,
    menu_callback_data: str | None = None,
    previous_page_callback_data: str | None = None,
    next_page_callback_data: str | None = None,
    extra_rows: Sequence[Sequence[InlineKeyboardButton]] | None = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for row in item_rows:
        builder.row(*row)
    if extra_rows:
        for row in extra_rows:
            builder.row(*row)
    if previous_page_callback_data or next_page_callback_data:
        nav_buttons: list[InlineKeyboardButton] = []
        if previous_page_callback_data:
            nav_buttons.append(InlineKeyboardButton(text="Назад", callback_data=previous_page_callback_data))
        if next_page_callback_data:
            nav_buttons.append(InlineKeyboardButton(text="Далее", callback_data=next_page_callback_data))
        builder.row(*nav_buttons)
    footer_buttons: list[InlineKeyboardButton] = []
    if back_callback_data:
        footer_buttons.append(InlineKeyboardButton(text="Назад", callback_data=back_callback_data))
    if menu_callback_data:
        footer_buttons.append(InlineKeyboardButton(text="В меню", callback_data=menu_callback_data))
    if footer_buttons:
        builder.row(*footer_buttons)
    return builder.as_markup()


def chunk_buttons(
    buttons: Sequence[InlineKeyboardButton],
    *,
    row_size: int,
) -> list[list[InlineKeyboardButton]]:
    safe_row_size = max(row_size, 1)
    return [
        list(buttons[index : index + safe_row_size])
        for index in range(0, len(buttons), safe_row_size)
    ]
