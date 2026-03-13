from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.dto.map_definition_dto import MapDefinitionDTO
from app.common.time_utils import utc_now
from app.domain.models.map_definition import MapDefinition
from app.infrastructure.persistence.models import MapCatalogModel


class MapCatalogRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def upsert_many(self, definitions: Sequence[MapDefinitionDTO]) -> list[MapDefinition]:
        now = utc_now()
        async with self._session_factory() as session:
            async with session.begin():
                rows = list((await session.execute(select(MapCatalogModel))).scalars())
                by_external = {row.external_id: row for row in rows if row.external_id}
                by_canonical = {row.canonical_name: row for row in rows}
                touched_ids: set[int] = set()

                for definition in definitions:
                    row = None
                    if definition.external_id:
                        row = by_external.get(definition.external_id)
                    if row is None:
                        row = by_canonical.get(definition.canonical_name)

                    if row is None:
                        row = MapCatalogModel(
                            external_id=definition.external_id,
                            canonical_name=definition.canonical_name,
                            display_name=definition.display_name,
                            aliases_json=list(definition.aliases),
                            is_active=definition.is_active,
                            last_seen_at=now,
                            updated_at=now,
                        )
                        session.add(row)
                        await session.flush()
                        if row.external_id:
                            by_external[row.external_id] = row
                        by_canonical[row.canonical_name] = row
                    else:
                        row.external_id = definition.external_id
                        row.canonical_name = definition.canonical_name
                        row.display_name = definition.display_name
                        row.aliases_json = list(definition.aliases)
                        row.is_active = definition.is_active
                        row.last_seen_at = now
                        row.updated_at = now

                    touched_ids.add(row.id)

                for row in rows:
                    if row.id not in touched_ids:
                        row.is_active = False
                        row.updated_at = now

            return await self.list_all()

    async def list_active(self) -> list[MapDefinition]:
        async with self._session_factory() as session:
            stmt = select(MapCatalogModel).where(MapCatalogModel.is_active.is_(True)).order_by(
                MapCatalogModel.display_name.asc()
            )
            rows = list((await session.execute(stmt)).scalars())
            return [self._to_domain(row) for row in rows]

    async def list_all(self) -> list[MapDefinition]:
        async with self._session_factory() as session:
            stmt = select(MapCatalogModel).order_by(MapCatalogModel.display_name.asc())
            rows = list((await session.execute(stmt)).scalars())
            return [self._to_domain(row) for row in rows]

    async def get_by_id(self, catalog_id: int) -> MapDefinition | None:
        async with self._session_factory() as session:
            row = await session.get(MapCatalogModel, catalog_id)
            return None if row is None else self._to_domain(row)

    async def resolve_catalog_id(
        self,
        *,
        external_id: str | None,
        canonical_name: str,
    ) -> int | None:
        async with self._session_factory() as session:
            predicates = [MapCatalogModel.canonical_name == canonical_name]
            if external_id:
                predicates.insert(0, MapCatalogModel.external_id == external_id)
            stmt = select(MapCatalogModel).where(or_(*predicates)).order_by(MapCatalogModel.id.asc())
            rows = list((await session.execute(stmt)).scalars())
            if not rows:
                return None
            if external_id:
                for row in rows:
                    if row.external_id == external_id:
                        return row.id
            return rows[0].id

    @staticmethod
    def _to_domain(row: MapCatalogModel) -> MapDefinition:
        return MapDefinition(
            id=row.id,
            external_id=row.external_id,
            canonical_name=row.canonical_name,
            display_name=row.display_name,
            aliases=tuple(row.aliases_json or []),
            is_active=row.is_active,
            last_seen_at=row.last_seen_at,
            updated_at=row.updated_at,
        )

