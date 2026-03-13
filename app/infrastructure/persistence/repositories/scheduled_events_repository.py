from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.common.time_utils import ensure_utc, utc_now
from app.domain.models.scheduled_event import ScheduledEvent
from app.infrastructure.persistence.models import ScheduledEventCacheModel


class ScheduledEventsRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def refresh(self, events: Sequence[ScheduledEvent]) -> list[ScheduledEvent]:
        now = utc_now()
        async with self._session_factory() as session:
            async with session.begin():
                existing_rows = list((await session.execute(select(ScheduledEventCacheModel))).scalars())
                existing_by_source = {row.source_id: row for row in existing_rows}
                incoming_source_ids = {event.source_id for event in events}

                for event in events:
                    row = existing_by_source.get(event.source_id)
                    if row is None:
                        row = ScheduledEventCacheModel(
                            source_id=event.source_id,
                            event_catalog_id=event.event_catalog_id,
                            map_catalog_id=event.map_catalog_id,
                            event_display_name=event.event_display_name,
                            map_display_name=event.map_display_name,
                            starts_at=event.starts_at,
                            ends_at=event.ends_at,
                            raw_payload=dict(event.metadata),
                            fetched_at=now,
                        )
                        session.add(row)
                    else:
                        row.event_catalog_id = event.event_catalog_id
                        row.map_catalog_id = event.map_catalog_id
                        row.event_display_name = event.event_display_name
                        row.map_display_name = event.map_display_name
                        row.starts_at = event.starts_at
                        row.ends_at = event.ends_at
                        row.raw_payload = dict(event.metadata)
                        row.fetched_at = now

                stale_source_ids = [row.source_id for row in existing_rows if row.source_id not in incoming_source_ids]
                if stale_source_ids:
                    await session.execute(
                        delete(ScheduledEventCacheModel).where(
                            ScheduledEventCacheModel.source_id.in_(stale_source_ids)
                        )
                    )

            return await self.list_future(now=now)

    async def list_future(
        self,
        *,
        now: datetime,
        event_catalog_id: int | None = None,
        map_catalog_id: int | None = None,
    ) -> list[ScheduledEvent]:
        async with self._session_factory() as session:
            stmt = select(ScheduledEventCacheModel).where(ScheduledEventCacheModel.starts_at >= now)
            if event_catalog_id is not None:
                stmt = stmt.where(ScheduledEventCacheModel.event_catalog_id == event_catalog_id)
            if map_catalog_id is not None:
                stmt = stmt.where(ScheduledEventCacheModel.map_catalog_id == map_catalog_id)
            stmt = stmt.order_by(ScheduledEventCacheModel.starts_at.asc())
            rows = list((await session.execute(stmt)).scalars())
            return [self._to_domain(row) for row in rows]

    async def list_for_summary(
        self,
        *,
        now: datetime,
        event_catalog_id: int | None = None,
        map_catalog_id: int | None = None,
    ) -> list[ScheduledEvent]:
        async with self._session_factory() as session:
            stmt = select(ScheduledEventCacheModel)
            if event_catalog_id is not None:
                stmt = stmt.where(ScheduledEventCacheModel.event_catalog_id == event_catalog_id)
            if map_catalog_id is not None:
                stmt = stmt.where(ScheduledEventCacheModel.map_catalog_id == map_catalog_id)
            stmt = stmt.where(
                (ScheduledEventCacheModel.starts_at >= now)
                | (ScheduledEventCacheModel.ends_at.is_not(None) & (ScheduledEventCacheModel.ends_at > now))
            )
            stmt = stmt.order_by(
                ScheduledEventCacheModel.event_display_name.asc(),
                ScheduledEventCacheModel.starts_at.asc(),
            )
            rows = list((await session.execute(stmt)).scalars())
            return [self._to_domain(row) for row in rows]

    async def get_by_id(self, scheduled_event_id: int) -> ScheduledEvent | None:
        async with self._session_factory() as session:
            row = await session.get(ScheduledEventCacheModel, scheduled_event_id)
            return None if row is None else self._to_domain(row)

    @staticmethod
    def _to_domain(row: ScheduledEventCacheModel) -> ScheduledEvent:
        return ScheduledEvent(
            id=row.id,
            source_id=row.source_id,
            event_catalog_id=row.event_catalog_id,
            map_catalog_id=row.map_catalog_id,
            event_display_name=row.event_display_name,
            map_display_name=row.map_display_name,
            starts_at=ensure_utc(row.starts_at),
            ends_at=None if row.ends_at is None else ensure_utc(row.ends_at),
            metadata=dict(row.raw_payload or {}),
        )
