from __future__ import annotations

from aiogram.types import InlineKeyboardButton

from app.bot.menu.markup import build_menu_keyboard, chunk_buttons


def test_chunk_buttons_splits_buttons_by_row_size() -> None:
    buttons = [InlineKeyboardButton(text=str(index), callback_data=f"cb:{index}") for index in range(5)]

    rows = chunk_buttons(buttons, row_size=2)

    assert [[button.text for button in row] for row in rows] == [["0", "1"], ["2", "3"], ["4"]]


def test_build_menu_keyboard_adds_pagination_and_footer_buttons() -> None:
    markup = build_menu_keyboard(
        item_rows=[[InlineKeyboardButton(text="One", callback_data="cb:1")]],
        back_callback_data="cb:back",
        menu_callback_data="cb:menu",
        previous_page_callback_data="cb:prev",
        next_page_callback_data="cb:next",
    )

    rows = [[button.text for button in row] for row in markup.inline_keyboard]

    assert rows == [["One"], ["Назад", "Далее"], ["Назад", "В меню"]]


def test_build_menu_keyboard_omits_missing_navigation_buttons() -> None:
    markup = build_menu_keyboard(
        item_rows=[],
        back_callback_data="cb:back",
        menu_callback_data="cb:menu",
    )

    rows = [[button.text for button in row] for row in markup.inline_keyboard]

    assert rows == [["Назад", "В меню"]]
