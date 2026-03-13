from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.application.exceptions import ValidationApplicationError
from app.common.timezone import ChatTimezoneContext, build_timezone_context, convert_utc_to_chat_local, format_chat_local_time
from app.infrastructure.persistence.repositories.chat_timezone_settings_repository import ChatTimezoneSettingsRepository


class TimezoneService:
    def __init__(self, chat_timezone_settings_repository: ChatTimezoneSettingsRepository) -> None:
        self._chat_timezone_settings_repository = chat_timezone_settings_repository

    async def get_chat_timezone(self, *, chat_id: int) -> ChatTimezoneContext:
        timezone_name = await self._chat_timezone_settings_repository.get_timezone(chat_id=chat_id)
        return build_timezone_context(chat_id=chat_id, timezone_name=timezone_name)

    async def set_chat_timezone(self, *, chat_id: int, timezone_name: str) -> ChatTimezoneContext:
        normalized = self._validate_timezone_name(timezone_name)
        await self._chat_timezone_settings_repository.set_timezone(chat_id=chat_id, timezone_name=normalized)
        return build_timezone_context(chat_id=chat_id, timezone_name=normalized)

    def convert_utc_to_chat_local(self, value: datetime, *, timezone_context: ChatTimezoneContext) -> datetime:
        return convert_utc_to_chat_local(value, timezone_context=timezone_context)

    def format_chat_local_time(self, value: datetime, *, timezone_context: ChatTimezoneContext) -> str:
        return format_chat_local_time(value, timezone_context=timezone_context)

    @staticmethod
    def _validate_timezone_name(timezone_name: str) -> str:
        normalized = timezone_name.strip()
        if not normalized:
            raise ValidationApplicationError("Timezone cannot be empty.")
        try:
            ZoneInfo(normalized)
        except ZoneInfoNotFoundError as exc:
            raise ValidationApplicationError(f"Unknown timezone: {timezone_name}") from exc
        return normalized
