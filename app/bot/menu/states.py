from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class MenuStates(StatesGroup):
    waiting_for_notification_input = State()
