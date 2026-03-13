from __future__ import annotations

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.enums.subscription_scope import SubscriptionScope
from app.domain.models.subscription import Subscription
from app.infrastructure.persistence.models import SubscriptionModel


class SubscriptionsRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_active(
        self,
        *,
        chat_id: int,
        scope_type: SubscriptionScope,
        event_catalog_id: int | None,
        map_catalog_id: int | None,
    ) -> Subscription | None:
        async with self._session_factory() as session:
            stmt = (
                select(SubscriptionModel)
                .where(SubscriptionModel.chat_id == chat_id)
                .where(SubscriptionModel.scope_type == scope_type)
                .where(SubscriptionModel.is_enabled.is_(True))
                .where(
                    and_(
                        SubscriptionModel.event_catalog_id.is_(None)
                        if event_catalog_id is None
                        else SubscriptionModel.event_catalog_id == event_catalog_id,
                        SubscriptionModel.map_catalog_id.is_(None)
                        if map_catalog_id is None
                        else SubscriptionModel.map_catalog_id == map_catalog_id,
                    )
                )
                .order_by(SubscriptionModel.id.asc())
            )
            row = (await session.execute(stmt)).scalars().first()
            return None if row is None else self._to_domain(row)

    async def add(
        self,
        *,
        chat_id: int,
        scope_type: SubscriptionScope,
        event_catalog_id: int | None,
        map_catalog_id: int | None,
    ) -> Subscription:
        async with self._session_factory() as session:
            async with session.begin():
                row = SubscriptionModel(
                    chat_id=chat_id,
                    scope_type=scope_type,
                    event_catalog_id=event_catalog_id,
                    map_catalog_id=map_catalog_id,
                    is_enabled=True,
                )
                session.add(row)
                await session.flush()
                await session.refresh(row)
                return self._to_domain(row)

    async def disable(
        self,
        *,
        chat_id: int,
        scope_type: SubscriptionScope,
        event_catalog_id: int | None,
        map_catalog_id: int | None,
    ) -> int:
        async with self._session_factory() as session:
            async with session.begin():
                stmt = (
                    update(SubscriptionModel)
                    .where(SubscriptionModel.chat_id == chat_id)
                    .where(SubscriptionModel.scope_type == scope_type)
                    .where(SubscriptionModel.is_enabled.is_(True))
                    .where(
                        and_(
                            SubscriptionModel.event_catalog_id.is_(None)
                            if event_catalog_id is None
                            else SubscriptionModel.event_catalog_id == event_catalog_id,
                            SubscriptionModel.map_catalog_id.is_(None)
                            if map_catalog_id is None
                            else SubscriptionModel.map_catalog_id == map_catalog_id,
                        )
                    )
                    .values(is_enabled=False)
                )
                result = await session.execute(stmt)
                return int(result.rowcount or 0)

    async def disable_all(self, *, chat_id: int) -> int:
        async with self._session_factory() as session:
            async with session.begin():
                stmt = (
                    update(SubscriptionModel)
                    .where(SubscriptionModel.chat_id == chat_id)
                    .where(SubscriptionModel.is_enabled.is_(True))
                    .values(is_enabled=False)
                )
                result = await session.execute(stmt)
                return int(result.rowcount or 0)

    async def disable_by_id(self, *, chat_id: int, subscription_id: int) -> int:
        async with self._session_factory() as session:
            async with session.begin():
                stmt = (
                    update(SubscriptionModel)
                    .where(SubscriptionModel.id == subscription_id)
                    .where(SubscriptionModel.chat_id == chat_id)
                    .where(SubscriptionModel.is_enabled.is_(True))
                    .values(is_enabled=False)
                )
                result = await session.execute(stmt)
                return int(result.rowcount or 0)

    async def list_by_chat(self, *, chat_id: int) -> list[Subscription]:
        async with self._session_factory() as session:
            stmt = (
                select(SubscriptionModel)
                .where(SubscriptionModel.chat_id == chat_id)
                .where(SubscriptionModel.is_enabled.is_(True))
                .order_by(SubscriptionModel.created_at.asc())
            )
            rows = list((await session.execute(stmt)).scalars())
            return [self._to_domain(row) for row in rows]

    async def list_all_enabled(self) -> list[Subscription]:
        async with self._session_factory() as session:
            stmt = select(SubscriptionModel).where(SubscriptionModel.is_enabled.is_(True))
            rows = list((await session.execute(stmt)).scalars())
            return [self._to_domain(row) for row in rows]

    @staticmethod
    def _to_domain(row: SubscriptionModel) -> Subscription:
        return Subscription(
            id=row.id,
            chat_id=row.chat_id,
            scope_type=row.scope_type,
            event_catalog_id=row.event_catalog_id,
            map_catalog_id=row.map_catalog_id,
            is_enabled=row.is_enabled,
            created_at=row.created_at,
        )
