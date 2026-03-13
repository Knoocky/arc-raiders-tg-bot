from __future__ import annotations

from aiogram.types import InlineKeyboardButton

from app.application.exceptions import ValidationApplicationError
from app.application.services.catalog_service import CatalogService
from app.application.services.event_service import EventService
from app.application.services.notification_service import NotificationService
from app.application.services.subscription_service import SubscriptionService
from app.application.services.timezone_service import TimezoneService
from app.bot.formatters.help_formatter import build_help_text
from app.bot.formatters.notifications_formatter import format_offsets
from app.bot.formatters.subscription_actions_formatter import format_watch_result
from app.bot.formatters.subscription_formatter import format_subscription_scope
from app.bot.menu.callbacks import MenuAction, build_menu_callback
from app.bot.menu.markup import build_menu_keyboard, chunk_buttons
from app.bot.menu.pagination import paginate_items
from app.bot.menu.types import MenuScreen
from app.bot.parsers.command_parser import parse_notify_command
from app.bot.presenters.events_presenter import build_events_summary_text
from app.bot.presenters.subscriptions_presenter import build_subscriptions_overview_text
from app.domain.models.event_definition import EventDefinition
from app.domain.models.map_definition import MapDefinition


class MenuController:
    PAGE_SIZE = 8
    PRESET_OFFSETS = (5, 10, 15, 30, 45, 60, 90)

    def __init__(
        self,
        *,
        catalog_service: CatalogService,
        event_service: EventService,
        subscription_service: SubscriptionService,
        notification_service: NotificationService,
        timezone_service: TimezoneService,
    ) -> None:
        self._catalog_service = catalog_service
        self._event_service = event_service
        self._subscription_service = subscription_service
        self._notification_service = notification_service
        self._timezone_service = timezone_service

    async def build_root_screen(self) -> MenuScreen:
        rows = [
            [self._button("Подписаться на событие", build_menu_callback(MenuAction.SUBSCRIBE_EVENTS, 0))],
            [self._button("Отписаться от события", build_menu_callback(MenuAction.UNSUBSCRIBE_LIST, 0))],
            [self._button("Настроить уведомления", build_menu_callback(MenuAction.NOTIFICATIONS))],
            [self._button("Показать всё расписание", build_menu_callback(MenuAction.SCHEDULE_ALL))],
            [self._button("Показать расписание события", build_menu_callback(MenuAction.SCHEDULE_EVENTS, 0))],
            [self._button("Мои подписки", build_menu_callback(MenuAction.LIST))],
            [self._button("Помощь", build_menu_callback(MenuAction.HELP))],
        ]
        return MenuScreen(
            text="Главное меню\nВыберите действие.",
            keyboard=build_menu_keyboard(item_rows=rows),
        )

    async def build_help_screen(self) -> MenuScreen:
        return MenuScreen(
            text=build_help_text(),
            keyboard=build_menu_keyboard(
                item_rows=[],
                back_callback_data=build_menu_callback(MenuAction.ROOT),
                menu_callback_data=build_menu_callback(MenuAction.ROOT),
            ),
            parse_mode=None,
        )

    async def build_subscribe_events_screen(self, *, page: int) -> MenuScreen:
        events = await self._catalog_service.list_events_catalog()
        page_slice = paginate_items(events, page=page, page_size=self.PAGE_SIZE)
        rows = [
            [self._button(event.display_name, build_menu_callback(MenuAction.SUBSCRIBE_MAPS, event.id, page_slice.page, 0))]
            for event in page_slice.items
            if event.id is not None
        ]
        text = "Выберите событие для подписки." if rows else "Каталог событий пуст."
        return MenuScreen(
            text=text,
            keyboard=build_menu_keyboard(
                item_rows=rows,
                back_callback_data=build_menu_callback(MenuAction.ROOT),
                menu_callback_data=build_menu_callback(MenuAction.ROOT),
                previous_page_callback_data=self._page_callback(MenuAction.SUBSCRIBE_EVENTS, page_slice.page - 1)
                if page_slice.has_previous
                else None,
                next_page_callback_data=self._page_callback(MenuAction.SUBSCRIBE_EVENTS, page_slice.page + 1)
                if page_slice.has_next
                else None,
            ),
        )

    async def build_subscribe_maps_screen(
        self,
        *,
        event_id: int,
        event_page: int,
        page: int,
    ) -> MenuScreen:
        event = await self._get_event_or_raise(event_id)
        maps = await self._catalog_service.list_maps_catalog()
        page_slice = paginate_items(maps, page=page, page_size=self.PAGE_SIZE)
        rows = [[self._button("Любая карта", build_menu_callback(MenuAction.SUBSCRIBE_ANY_MAP, event_id, event_page, page_slice.page))]]
        rows.extend(
            [
                [self._button(map_item.display_name, build_menu_callback(MenuAction.SUBSCRIBE_MAP, event_id, map_item.id, event_page, page_slice.page))]
                for map_item in page_slice.items
                if map_item.id is not None
            ]
        )
        return MenuScreen(
            text=f"Событие: {event.display_name}\nВыберите карту или вариант «Любая карта».",
            keyboard=build_menu_keyboard(
                item_rows=rows,
                back_callback_data=build_menu_callback(MenuAction.SUBSCRIBE_EVENTS, event_page),
                menu_callback_data=build_menu_callback(MenuAction.ROOT),
                previous_page_callback_data=build_menu_callback(
                    MenuAction.SUBSCRIBE_MAPS,
                    event_id,
                    event_page,
                    page_slice.page - 1,
                )
                if page_slice.has_previous
                else None,
                next_page_callback_data=build_menu_callback(
                    MenuAction.SUBSCRIBE_MAPS,
                    event_id,
                    event_page,
                    page_slice.page + 1,
                )
                if page_slice.has_next
                else None,
            ),
        )

    async def create_event_subscription(
        self,
        *,
        chat_id: int,
        event_id: int,
        event_page: int,
        map_page: int,
        map_id: int | None,
    ) -> MenuScreen:
        event = await self._get_event_or_raise(event_id)
        map_item = await self._get_map_or_raise(map_id) if map_id is not None else None
        _, created = await self._subscription_service.subscribe(
            chat_id=chat_id,
            event_catalog_id=event.id,
            map_catalog_id=map_item.id if map_item is not None else None,
        )
        return MenuScreen(
            text=format_watch_result(
                created=created,
                event_display_name=event.display_name,
                map_display_name=None if map_item is None else map_item.display_name,
            ),
            keyboard=build_menu_keyboard(
                item_rows=[],
                back_callback_data=build_menu_callback(MenuAction.SUBSCRIBE_MAPS, event_id, event_page, map_page),
                menu_callback_data=build_menu_callback(MenuAction.ROOT),
            ),
        )

    async def build_unsubscribe_screen(self, *, chat_id: int, page: int) -> MenuScreen:
        subscriptions = await self._subscription_service.list_subscriptions(chat_id=chat_id)
        page_slice = paginate_items(subscriptions, page=page, page_size=self.PAGE_SIZE)
        rows = [
            [self._button(format_subscription_scope(subscription), build_menu_callback(MenuAction.UNSUBSCRIBE_ONE, subscription.subscription_id, page_slice.page))]
            for subscription in page_slice.items
            if subscription.subscription_id is not None
        ]
        extra_rows = (
            [[self._button("Отписаться от всех", build_menu_callback(MenuAction.UNSUBSCRIBE_ALL, page_slice.page))]]
            if subscriptions
            else None
        )
        text = "Выберите подписку для удаления." if subscriptions else "У этого чата нет активных подписок."
        return MenuScreen(
            text=text,
            keyboard=build_menu_keyboard(
                item_rows=rows,
                extra_rows=extra_rows,
                back_callback_data=build_menu_callback(MenuAction.ROOT),
                menu_callback_data=build_menu_callback(MenuAction.ROOT),
                previous_page_callback_data=self._page_callback(MenuAction.UNSUBSCRIBE_LIST, page_slice.page - 1)
                if page_slice.has_previous
                else None,
                next_page_callback_data=self._page_callback(MenuAction.UNSUBSCRIBE_LIST, page_slice.page + 1)
                if page_slice.has_next
                else None,
            ),
        )

    async def remove_subscription(self, *, chat_id: int, subscription_id: int, page: int) -> MenuScreen:
        label = await self._subscription_label(chat_id=chat_id, subscription_id=subscription_id)
        removed = await self._subscription_service.unsubscribe_by_id(chat_id=chat_id, subscription_id=subscription_id)
        text = f"Подписка удалена: {label}" if removed else "Подписка не найдена."
        return MenuScreen(
            text=text,
            keyboard=build_menu_keyboard(
                item_rows=[],
                back_callback_data=build_menu_callback(MenuAction.UNSUBSCRIBE_LIST, page),
                menu_callback_data=build_menu_callback(MenuAction.ROOT),
            ),
        )

    async def remove_all_subscriptions(self, *, chat_id: int, page: int) -> MenuScreen:
        removed = await self._subscription_service.unsubscribe_all(chat_id=chat_id)
        text = "Все подписки удалены." if removed else "Активных подписок нет."
        return MenuScreen(
            text=text,
            keyboard=build_menu_keyboard(
                item_rows=[],
                back_callback_data=build_menu_callback(MenuAction.UNSUBSCRIBE_LIST, page),
                menu_callback_data=build_menu_callback(MenuAction.ROOT),
            ),
        )

    async def build_notifications_screen(self, *, chat_id: int, notice: str | None = None) -> MenuScreen:
        offsets = await self._notification_service.list_offsets(chat_id=chat_id)
        text = "Настройка уведомлений\n" + format_offsets(offsets)
        if notice:
            text = f"{text}\n\n{notice}"
        rows = chunk_buttons(
            [self._button(f"+{offset}", build_menu_callback(MenuAction.NOTIFICATION_ADD, offset)) for offset in self.PRESET_OFFSETS],
            row_size=4,
        )
        if offsets:
            rows.extend(
                chunk_buttons(
                    [self._button(f"-{offset}", build_menu_callback(MenuAction.NOTIFICATION_REMOVE, offset)) for offset in offsets],
                    row_size=4,
                )
            )
            rows.append([self._button("Сбросить всё", build_menu_callback(MenuAction.NOTIFICATION_CLEAR))])
        rows.append([self._button("Ввести вручную", build_menu_callback(MenuAction.NOTIFICATION_CUSTOM))])
        return MenuScreen(
            text=text,
            keyboard=build_menu_keyboard(
                item_rows=rows,
                back_callback_data=build_menu_callback(MenuAction.ROOT),
                menu_callback_data=build_menu_callback(MenuAction.ROOT),
            ),
        )

    async def add_notification_offset(self, *, chat_id: int, minutes: int) -> MenuScreen:
        await self._notification_service.add_offsets(chat_id=chat_id, minutes=(minutes,))
        return await self.build_notifications_screen(chat_id=chat_id, notice=f"Добавлено смещение: {minutes} мин.")

    async def remove_notification_offset(self, *, chat_id: int, minutes: int) -> MenuScreen:
        await self._notification_service.remove_offsets(chat_id=chat_id, minutes=(minutes,))
        return await self.build_notifications_screen(chat_id=chat_id, notice=f"Удалено смещение: {minutes} мин.")

    async def clear_notification_offsets(self, *, chat_id: int) -> MenuScreen:
        await self._notification_service.clear_offsets(chat_id=chat_id)
        return await self.build_notifications_screen(chat_id=chat_id, notice="Все смещения уведомлений сброшены.")

    async def build_custom_notification_prompt(self, *, chat_id: int, notice: str | None = None) -> MenuScreen:
        offsets = await self._notification_service.list_offsets(chat_id=chat_id)
        text = (
            "Введите значения уведомлений.\n"
            f"{format_offsets(offsets)}\n\n"
            "Примеры:\n"
            "5 15 30\n"
            "add 90\n"
            "remove 15\n"
            "list"
        )
        if notice:
            text = f"{text}\n\n{notice}"
        return MenuScreen(
            text=text,
            keyboard=build_menu_keyboard(
                item_rows=[],
                back_callback_data=build_menu_callback(MenuAction.NOTIFICATIONS),
                menu_callback_data=build_menu_callback(MenuAction.ROOT),
            ),
            parse_mode=None,
        )

    async def apply_custom_notification_input(self, *, chat_id: int, raw_text: str) -> MenuScreen:
        normalized = raw_text.strip()
        if normalized.casefold().startswith("/notify"):
            normalized = normalized[7:].strip()
        parsed = parse_notify_command(normalized)
        if parsed.action == "list":
            return await self.build_notifications_screen(chat_id=chat_id)
        if parsed.action == "replace":
            await self._notification_service.replace_offsets(chat_id=chat_id, minutes=parsed.minutes)
            return await self.build_notifications_screen(chat_id=chat_id, notice="Смещения уведомлений заменены.")
        if parsed.action == "add":
            await self._notification_service.add_offsets(chat_id=chat_id, minutes=parsed.minutes)
            return await self.build_notifications_screen(chat_id=chat_id, notice="Смещения уведомлений обновлены.")
        await self._notification_service.remove_offsets(chat_id=chat_id, minutes=parsed.minutes)
        return await self.build_notifications_screen(chat_id=chat_id, notice="Смещения уведомлений обновлены.")

    async def build_all_schedule_screen(self, *, chat_id: int) -> MenuScreen:
        return MenuScreen(
            text=await build_events_summary_text(
                chat_id=chat_id,
                event_service=self._event_service,
                timezone_service=self._timezone_service,
                max_future_lines_per_group=1,
            ),
            keyboard=build_menu_keyboard(
                item_rows=[],
                back_callback_data=build_menu_callback(MenuAction.ROOT),
                menu_callback_data=build_menu_callback(MenuAction.ROOT),
            ),
        )

    async def build_schedule_event_picker_screen(self, *, page: int) -> MenuScreen:
        events = await self._catalog_service.list_events_catalog()
        page_slice = paginate_items(events, page=page, page_size=self.PAGE_SIZE)
        rows = [
            [self._button(event.display_name, build_menu_callback(MenuAction.SCHEDULE_EVENT, event.id, page_slice.page))]
            for event in page_slice.items
            if event.id is not None
        ]
        text = "Выберите событие для просмотра расписания." if rows else "Каталог событий пуст."
        return MenuScreen(
            text=text,
            keyboard=build_menu_keyboard(
                item_rows=rows,
                back_callback_data=build_menu_callback(MenuAction.ROOT),
                menu_callback_data=build_menu_callback(MenuAction.ROOT),
                previous_page_callback_data=self._page_callback(MenuAction.SCHEDULE_EVENTS, page_slice.page - 1)
                if page_slice.has_previous
                else None,
                next_page_callback_data=self._page_callback(MenuAction.SCHEDULE_EVENTS, page_slice.page + 1)
                if page_slice.has_next
                else None,
            ),
        )

    async def build_event_schedule_screen(self, *, chat_id: int, event_id: int, page: int) -> MenuScreen:
        event = await self._get_event_or_raise(event_id)
        return MenuScreen(
            text=await build_events_summary_text(
                chat_id=chat_id,
                event_service=self._event_service,
                timezone_service=self._timezone_service,
                event_catalog_id=event.id,
            ),
            keyboard=build_menu_keyboard(
                item_rows=[],
                back_callback_data=build_menu_callback(MenuAction.SCHEDULE_EVENTS, page),
                menu_callback_data=build_menu_callback(MenuAction.ROOT),
            ),
        )

    async def build_my_subscriptions_screen(self, *, chat_id: int) -> MenuScreen:
        return MenuScreen(
            text=await build_subscriptions_overview_text(
                chat_id=chat_id,
                subscription_service=self._subscription_service,
                notification_service=self._notification_service,
            ),
            keyboard=build_menu_keyboard(
                item_rows=[],
                back_callback_data=build_menu_callback(MenuAction.ROOT),
                menu_callback_data=build_menu_callback(MenuAction.ROOT),
            ),
        )

    @staticmethod
    def _button(text: str, callback_data: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(text=text, callback_data=callback_data)

    @staticmethod
    def _page_callback(action: str, page: int) -> str:
        return build_menu_callback(action, page)

    async def _get_event_or_raise(self, event_id: int) -> EventDefinition:
        event = await self._catalog_service.get_event_by_id(event_id=event_id)
        if event is None or event.id is None:
            raise ValidationApplicationError("Selected event is no longer available.")
        return event

    async def _get_map_or_raise(self, map_id: int) -> MapDefinition:
        map_item = await self._catalog_service.get_map_by_id(map_id=map_id)
        if map_item is None or map_item.id is None:
            raise ValidationApplicationError("Selected map is no longer available.")
        return map_item

    async def _subscription_label(self, *, chat_id: int, subscription_id: int) -> str:
        subscriptions = await self._subscription_service.list_subscriptions(chat_id=chat_id)
        selected = next(
            (subscription for subscription in subscriptions if subscription.subscription_id == subscription_id),
            None,
        )
        return "неизвестная подписка" if selected is None else format_subscription_scope(selected)
