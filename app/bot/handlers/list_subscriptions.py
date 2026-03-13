from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.application.services.notification_service import NotificationService
from app.application.services.subscription_service import SubscriptionService
from app.bot.presenters.subscriptions_presenter import build_subscriptions_overview_text


def register_list_handlers(
    router: Router,
    *,
    subscription_service: SubscriptionService,
    notification_service: NotificationService,
    ) -> None:
    @router.message(Command("list"))
    async def list_handler(message: Message) -> None:
        await message.answer(
            await build_subscriptions_overview_text(
                chat_id=message.chat.id,
                subscription_service=subscription_service,
                notification_service=notification_service,
            )
        )
