from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.persistence.models import ChatNotificationSettingModel


class NotificationSettingsRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def list_for_chat(self, *, chat_id: int) -> list[int]:
        async with self._session_factory() as session:
            stmt = (
                select(ChatNotificationSettingModel)
                .where(ChatNotificationSettingModel.chat_id == chat_id)
                .order_by(ChatNotificationSettingModel.minutes_before.desc())
            )
            rows = list((await session.execute(stmt)).scalars())
            return [row.minutes_before for row in rows]

    async def list_for_chats(self, *, chat_ids: Sequence[int]) -> dict[int, list[int]]:
        if not chat_ids:
            return {}

        async with self._session_factory() as session:
            stmt = (
                select(ChatNotificationSettingModel)
                .where(ChatNotificationSettingModel.chat_id.in_(list(chat_ids)))
                .order_by(
                    ChatNotificationSettingModel.chat_id.asc(),
                    ChatNotificationSettingModel.minutes_before.desc(),
                )
            )
            rows = list((await session.execute(stmt)).scalars())
            grouped: dict[int, list[int]] = defaultdict(list)
            for row in rows:
                grouped[row.chat_id].append(row.minutes_before)
            return dict(grouped)

    async def replace_for_chat(self, *, chat_id: int, minutes: Sequence[int]) -> list[int]:
        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    delete(ChatNotificationSettingModel).where(ChatNotificationSettingModel.chat_id == chat_id)
                )
                for minute in minutes:
                    session.add(ChatNotificationSettingModel(chat_id=chat_id, minutes_before=minute))
            return await self.list_for_chat(chat_id=chat_id)

    async def add_for_chat(self, *, chat_id: int, minutes: Sequence[int]) -> list[int]:
        existing = set(await self.list_for_chat(chat_id=chat_id))
        to_add = sorted({*existing, *minutes}, reverse=True)
        return await self.replace_for_chat(chat_id=chat_id, minutes=to_add)

    async def remove_for_chat(self, *, chat_id: int, minutes: Sequence[int]) -> list[int]:
        remaining = sorted(set(await self.list_for_chat(chat_id=chat_id)) - set(minutes), reverse=True)
        return await self.replace_for_chat(chat_id=chat_id, minutes=remaining)

    async def clear_for_chat(self, *, chat_id: int) -> list[int]:
        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    delete(ChatNotificationSettingModel).where(ChatNotificationSettingModel.chat_id == chat_id)
                )
        return []
