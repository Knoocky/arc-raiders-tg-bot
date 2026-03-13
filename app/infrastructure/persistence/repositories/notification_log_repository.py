from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.persistence.models import NotificationLogModel


class NotificationLogRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def has_sent(
        self,
        *,
        chat_id: int,
        scheduled_event_id: int,
        minutes_before: int,
    ) -> bool:
        async with self._session_factory() as session:
            stmt = (
                select(NotificationLogModel.id)
                .where(NotificationLogModel.chat_id == chat_id)
                .where(NotificationLogModel.scheduled_event_id == scheduled_event_id)
                .where(NotificationLogModel.minutes_before == minutes_before)
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    async def create(
        self,
        *,
        chat_id: int,
        scheduled_event_id: int,
        minutes_before: int,
    ) -> bool:
        async with self._session_factory() as session:
            try:
                async with session.begin():
                    session.add(
                        NotificationLogModel(
                            chat_id=chat_id,
                            scheduled_event_id=scheduled_event_id,
                            minutes_before=minutes_before,
                        )
                    )
                    await session.flush()
            except IntegrityError:
                return False
            return True
