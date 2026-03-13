from __future__ import annotations

from app.application.services.notification_service import NotificationService
from app.application.services.subscription_service import SubscriptionService
from app.bot.formatters.notifications_formatter import format_offsets
from app.bot.formatters.subscription_formatter import format_subscriptions


async def build_subscriptions_overview_text(
    *,
    chat_id: int,
    subscription_service: SubscriptionService,
    notification_service: NotificationService,
) -> str:
    subscriptions = await subscription_service.list_subscriptions(chat_id=chat_id)
    offsets = await notification_service.list_offsets(chat_id=chat_id)
    return format_subscriptions(subscriptions) + "\n\n" + format_offsets(offsets)
