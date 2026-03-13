from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.persistence.models import ChatTimezoneSettingModel


class ChatTimezoneSettingsRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_timezone(self, *, chat_id: int) -> str | None:
        async with self._session_factory() as session:
            stmt = select(ChatTimezoneSettingModel).where(ChatTimezoneSettingModel.chat_id == chat_id)
            row = (await session.execute(stmt)).scalar_one_or_none()
            return None if row is None else row.timezone

    async def set_timezone(self, *, chat_id: int, timezone_name: str) -> str:
        async with self._session_factory() as session:
            async with session.begin():
                stmt = select(ChatTimezoneSettingModel).where(ChatTimezoneSettingModel.chat_id == chat_id)
                row = (await session.execute(stmt)).scalar_one_or_none()
                if row is None:
                    session.add(ChatTimezoneSettingModel(chat_id=chat_id, timezone=timezone_name))
                else:
                    row.timezone = timezone_name
        return timezone_name

    async def clear_timezone(self, *, chat_id: int) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(delete(ChatTimezoneSettingModel).where(ChatTimezoneSettingModel.chat_id == chat_id))
