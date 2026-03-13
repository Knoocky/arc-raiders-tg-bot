from __future__ import annotations

from dataclasses import dataclass, field

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.application.exceptions import ApplicationError
from app.bot.menu.callbacks import MenuAction, MenuCallback, parse_menu_callback
from app.bot.menu.controller import MenuController
from app.bot.menu.render import answer_with_menu_screen, edit_message_with_menu_screen, edit_with_menu_screen
from app.bot.menu.states import MenuStates
from app.bot.menu.types import MenuScreen


@dataclass(slots=True, frozen=True)
class MenuRouteResult:
    screen: MenuScreen
    state_name: str | None = None
    state_data: dict[str, int | str] = field(default_factory=dict)


def register_menu_handlers(
    router: Router,
    *,
    menu_controller: MenuController,
) -> None:
    @router.message(Command("start", "menu"))
    async def menu_entrypoint(message: Message, state: FSMContext) -> None:
        await state.clear()
        await answer_with_menu_screen(message, await menu_controller.build_root_screen())

    @router.callback_query(F.data.startswith("m:"))
    async def menu_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
        parsed = parse_menu_callback(callback.data)
        if parsed is None:
            await callback.answer()
            return

        try:
            result = await route_menu_callback(
                parsed=parsed,
                callback=callback,
                menu_controller=menu_controller,
            )
        except ApplicationError as exc:
            await callback.answer(str(exc), show_alert=True)
            return

        if result.state_name is None:
            await state.clear()
        else:
            await state.set_state(result.state_name)
            await state.update_data(**result.state_data)

        await edit_with_menu_screen(callback, result.screen)
        await callback.answer()

    @router.message(StateFilter(MenuStates.waiting_for_notification_input))
    async def custom_notification_input_handler(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        menu_message_id = int(data.get("menu_message_id", 0))
        if menu_message_id <= 0:
            await state.clear()
            return

        try:
            screen = await menu_controller.apply_custom_notification_input(
                chat_id=message.chat.id,
                raw_text=message.text or "",
            )
        except ApplicationError as exc:
            screen = await menu_controller.build_custom_notification_prompt(
                chat_id=message.chat.id,
                notice=str(exc),
            )
            await edit_message_with_menu_screen(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=menu_message_id,
                screen=screen,
            )
            return

        await edit_message_with_menu_screen(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=menu_message_id,
            screen=screen,
        )
        await state.clear()


async def route_menu_callback(
    *,
    parsed: MenuCallback,
    callback: CallbackQuery,
    menu_controller: MenuController,
) -> MenuRouteResult:
    chat_id = callback.message.chat.id if callback.message is not None else callback.from_user.id
    message_id = callback.message.message_id if callback.message is not None else 0

    if parsed.action == MenuAction.ROOT:
        return MenuRouteResult(screen=await menu_controller.build_root_screen())
    if parsed.action == MenuAction.HELP:
        return MenuRouteResult(screen=await menu_controller.build_help_screen())
    if parsed.action == MenuAction.SUBSCRIBE_EVENTS:
        return MenuRouteResult(
            screen=await menu_controller.build_subscribe_events_screen(page=_int_part(parsed, 0)),
        )
    if parsed.action == MenuAction.SUBSCRIBE_MAPS:
        return MenuRouteResult(
            screen=await menu_controller.build_subscribe_maps_screen(
                event_id=_int_part(parsed, 0),
                event_page=_int_part(parsed, 1),
                page=_int_part(parsed, 2),
            )
        )
    if parsed.action == MenuAction.SUBSCRIBE_ANY_MAP:
        return MenuRouteResult(
            screen=await menu_controller.create_event_subscription(
                chat_id=chat_id,
                event_id=_int_part(parsed, 0),
                event_page=_int_part(parsed, 1),
                map_page=_int_part(parsed, 2),
                map_id=None,
            )
        )
    if parsed.action == MenuAction.SUBSCRIBE_MAP:
        return MenuRouteResult(
            screen=await menu_controller.create_event_subscription(
                chat_id=chat_id,
                event_id=_int_part(parsed, 0),
                map_id=_int_part(parsed, 1),
                event_page=_int_part(parsed, 2),
                map_page=_int_part(parsed, 3),
            )
        )
    if parsed.action == MenuAction.UNSUBSCRIBE_LIST:
        return MenuRouteResult(
            screen=await menu_controller.build_unsubscribe_screen(
                chat_id=chat_id,
                page=_int_part(parsed, 0),
            )
        )
    if parsed.action == MenuAction.UNSUBSCRIBE_ONE:
        return MenuRouteResult(
            screen=await menu_controller.remove_subscription(
                chat_id=chat_id,
                subscription_id=_int_part(parsed, 0),
                page=_int_part(parsed, 1),
            )
        )
    if parsed.action == MenuAction.UNSUBSCRIBE_ALL:
        return MenuRouteResult(
            screen=await menu_controller.remove_all_subscriptions(
                chat_id=chat_id,
                page=_int_part(parsed, 0),
            )
        )
    if parsed.action == MenuAction.NOTIFICATIONS:
        return MenuRouteResult(screen=await menu_controller.build_notifications_screen(chat_id=chat_id))
    if parsed.action == MenuAction.NOTIFICATION_ADD:
        return MenuRouteResult(
            screen=await menu_controller.add_notification_offset(
                chat_id=chat_id,
                minutes=_int_part(parsed, 0),
            )
        )
    if parsed.action == MenuAction.NOTIFICATION_REMOVE:
        return MenuRouteResult(
            screen=await menu_controller.remove_notification_offset(
                chat_id=chat_id,
                minutes=_int_part(parsed, 0),
            )
        )
    if parsed.action == MenuAction.NOTIFICATION_CLEAR:
        return MenuRouteResult(screen=await menu_controller.clear_notification_offsets(chat_id=chat_id))
    if parsed.action == MenuAction.NOTIFICATION_CUSTOM:
        return MenuRouteResult(
            screen=await menu_controller.build_custom_notification_prompt(chat_id=chat_id),
            state_name=MenuStates.waiting_for_notification_input.state,
            state_data={
                "chat_id": chat_id,
                "menu_message_id": message_id,
                "back_callback_data": "m:nb",
                "page": 0,
            },
        )
    if parsed.action == MenuAction.SCHEDULE_ALL:
        return MenuRouteResult(screen=await menu_controller.build_all_schedule_screen(chat_id=chat_id))
    if parsed.action == MenuAction.SCHEDULE_EVENTS:
        return MenuRouteResult(
            screen=await menu_controller.build_schedule_event_picker_screen(page=_int_part(parsed, 0)),
        )
    if parsed.action == MenuAction.SCHEDULE_EVENT:
        return MenuRouteResult(
            screen=await menu_controller.build_event_schedule_screen(
                chat_id=chat_id,
                event_id=_int_part(parsed, 0),
                page=_int_part(parsed, 1),
            )
        )
    if parsed.action == MenuAction.LIST:
        return MenuRouteResult(screen=await menu_controller.build_my_subscriptions_screen(chat_id=chat_id))
    return MenuRouteResult(screen=await menu_controller.build_root_screen())


def _int_part(parsed: MenuCallback, index: int, default: int = 0) -> int:
    if index >= len(parsed.parts):
        return default
    return int(parsed.parts[index])
