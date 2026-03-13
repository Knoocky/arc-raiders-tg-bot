from __future__ import annotations

from types import SimpleNamespace

from app.bot.handlers.menu import route_menu_callback
from app.bot.menu.callbacks import MenuAction, MenuCallback
from app.bot.menu.states import MenuStates
from app.bot.menu.types import MenuScreen


class RecordingMenuController:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[int, ...]]] = []

    async def build_root_screen(self) -> MenuScreen:
        self.calls.append(("root", ()))
        return MenuScreen(text="root", keyboard=SimpleNamespace(inline_keyboard=[]))

    async def build_help_screen(self) -> MenuScreen:
        self.calls.append(("help", ()))
        return MenuScreen(text="help", keyboard=SimpleNamespace(inline_keyboard=[]), parse_mode=None)

    async def build_custom_notification_prompt(self, *, chat_id: int) -> MenuScreen:
        self.calls.append(("custom_prompt", (chat_id,)))
        return MenuScreen(text="prompt", keyboard=SimpleNamespace(inline_keyboard=[]), parse_mode=None)

    async def create_event_subscription(
        self,
        *,
        chat_id: int,
        event_id: int,
        event_page: int,
        map_page: int,
        map_id: int | None,
    ) -> MenuScreen:
        self.calls.append(("subscribe", (chat_id, event_id, event_page, map_page, -1 if map_id is None else map_id)))
        return MenuScreen(text="subscribe", keyboard=SimpleNamespace(inline_keyboard=[]))


async def test_route_menu_callback_routes_subscription_action() -> None:
    controller = RecordingMenuController()
    callback = SimpleNamespace(
        message=SimpleNamespace(chat=SimpleNamespace(id=501), message_id=42),
        from_user=SimpleNamespace(id=700),
    )

    result = await route_menu_callback(
        parsed=MenuCallback(action=MenuAction.SUBSCRIBE_MAP, parts=("3", "9", "1", "2")),
        callback=callback,
        menu_controller=controller,
    )

    assert result.screen.text == "subscribe"
    assert controller.calls == [("subscribe", (501, 3, 1, 2, 9))]


async def test_route_menu_callback_enters_custom_notification_state() -> None:
    controller = RecordingMenuController()
    callback = SimpleNamespace(
        message=SimpleNamespace(chat=SimpleNamespace(id=-1001), message_id=77),
        from_user=SimpleNamespace(id=700),
    )

    result = await route_menu_callback(
        parsed=MenuCallback(action=MenuAction.NOTIFICATION_CUSTOM, parts=()),
        callback=callback,
        menu_controller=controller,
    )

    assert result.screen.text == "prompt"
    assert result.state_name == MenuStates.waiting_for_notification_input.state
    assert result.state_data["chat_id"] == -1001
    assert result.state_data["menu_message_id"] == 77


async def test_route_menu_callback_falls_back_to_root_for_unknown_action() -> None:
    controller = RecordingMenuController()
    callback = SimpleNamespace(
        message=SimpleNamespace(chat=SimpleNamespace(id=1), message_id=2),
        from_user=SimpleNamespace(id=3),
    )

    result = await route_menu_callback(
        parsed=MenuCallback(action="??", parts=()),
        callback=callback,
        menu_controller=controller,
    )

    assert result.screen.text == "root"
    assert controller.calls == [("root", ())]
