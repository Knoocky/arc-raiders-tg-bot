from __future__ import annotations

from dataclasses import dataclass

from aiogram.types import InlineKeyboardMarkup


@dataclass(slots=True, frozen=True)
class MenuScreen:
    text: str
    keyboard: InlineKeyboardMarkup
    parse_mode: str | None = "HTML"
