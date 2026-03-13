from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta
from typing import Protocol

from app.application.exceptions import ValidationApplicationError
from app.application.services.event_service import EventService
from app.application.services.subscription_service import SubscriptionService
from app.application.services.timezone_service import TimezoneService
from app.common.timezone import ChatTimezoneContext
from app.common.time_utils import ensure_utc, utc_now
from app.domain.models.scheduled_event import ScheduledEvent
from app.infrastructure.persistence.repositories.notification_log_repository import NotificationLogRepository
from app.infrastructure.persistence.repositories.notification_settings_repository import NotificationSettingsRepository

logger = logging.getLogger(__name__)


class NotificationSender(Protocol):
    async def send_message(self, chat_id: int, text: str) -> None:
        ...


class NotificationService:
    def __init__(
        self,
        *,
        event_service: EventService,
        subscription_service: SubscriptionService,
        timezone_service: TimezoneService,
        notification_settings_repository: NotificationSettingsRepository,
        notification_log_repository: NotificationLogRepository,
        sender: NotificationSender,
        message_formatter: Callable[[ScheduledEvent, int, datetime, ChatTimezoneContext], str],
    ) -> None:
        self._event_service = event_service
        self._subscription_service = subscription_service
        self._timezone_service = timezone_service
        self._notification_settings_repository = notification_settings_repository
        self._notification_log_repository = notification_log_repository
        self._sender = sender
        self._message_formatter = message_formatter

    async def replace_offsets(self, *, chat_id: int, minutes: Sequence[int]) -> list[int]:
        normalized = self._normalize_offsets(minutes)
        return await self._notification_settings_repository.replace_for_chat(chat_id=chat_id, minutes=normalized)

    async def add_offsets(self, *, chat_id: int, minutes: Sequence[int]) -> list[int]:
        normalized = self._normalize_offsets(minutes)
        return await self._notification_settings_repository.add_for_chat(chat_id=chat_id, minutes=normalized)

    async def remove_offsets(self, *, chat_id: int, minutes: Sequence[int]) -> list[int]:
        normalized = self._normalize_offsets(minutes)
        return await self._notification_settings_repository.remove_for_chat(chat_id=chat_id, minutes=normalized)

    async def clear_offsets(self, *, chat_id: int) -> list[int]:
        return await self._notification_settings_repository.clear_for_chat(chat_id=chat_id)

    async def list_offsets(self, *, chat_id: int) -> list[int]:
        return await self._notification_settings_repository.list_for_chat(chat_id=chat_id)

    async def dispatch_due_notifications(self, *, now: datetime | None = None) -> int:
        current_time = ensure_utc(now or utc_now())
        subscriptions = await self._subscription_service.list_all_enabled()
        if not subscriptions:
            return 0

        chat_ids = sorted({subscription.chat_id for subscription in subscriptions})
        offsets_by_chat = await self._notification_settings_repository.list_for_chats(chat_ids=chat_ids)
        max_offset = max((max(offsets) for offsets in offsets_by_chat.values() if offsets), default=0)
        if max_offset <= 0:
            return 0

        all_events = await self._event_service.list_upcoming_events(now=current_time)
        window_end = current_time + timedelta(minutes=max_offset)
        candidate_events = [event for event in all_events if event.starts_at <= window_end]
        sent_count = 0

        for event in candidate_events:
            if event.id is None:
                continue
            matching_chat_ids = {subscription.chat_id for subscription in subscriptions if subscription.matches(event)}
            for chat_id in matching_chat_ids:
                timezone_context = await self._timezone_service.get_chat_timezone(chat_id=chat_id)
                for offset in offsets_by_chat.get(chat_id, []):
                    if not self.should_send_notification(event.starts_at, now=current_time, minutes_before=offset):
                        continue
                    if await self._notification_log_repository.has_sent(
                        chat_id=chat_id,
                        scheduled_event_id=event.id,
                        minutes_before=offset,
                    ):
                        continue
                    message = self._message_formatter(event, offset, current_time, timezone_context)
                    try:
                        await self._sender.send_message(chat_id=chat_id, text=message)
                    except Exception:
                        logger.exception(
                            "Failed to send notification",
                            extra={
                                "chat_id": chat_id,
                                "scheduled_event_id": event.id,
                                "minutes_before": offset,
                            },
                        )
                        continue

                    created = await self._notification_log_repository.create(
                        chat_id=chat_id,
                        scheduled_event_id=event.id,
                        minutes_before=offset,
                    )
                    if created:
                        sent_count += 1

        return sent_count

    @staticmethod
    def should_send_notification(
        starts_at: datetime,
        *,
        now: datetime,
        minutes_before: int,
    ) -> bool:
        remaining_seconds = (ensure_utc(starts_at) - ensure_utc(now)).total_seconds()
        if remaining_seconds <= 0:
            return False
        upper_bound = minutes_before * 60
        lower_bound = (minutes_before - 1) * 60
        return lower_bound < remaining_seconds <= upper_bound

    @staticmethod
    def _normalize_offsets(minutes: Sequence[int]) -> list[int]:
        if not minutes:
            raise ValidationApplicationError("Provide at least one positive minute offset.")
        try:
            normalized = sorted({int(minute) for minute in minutes}, reverse=True)
        except (TypeError, ValueError) as exc:
            raise ValidationApplicationError("Notification offsets must be positive integers.") from exc
        if any(minute <= 0 for minute in normalized):
            raise ValidationApplicationError("Notification offsets must be positive integers.")
        return normalized
