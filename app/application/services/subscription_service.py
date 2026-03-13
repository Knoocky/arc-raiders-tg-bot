from __future__ import annotations

from dataclasses import dataclass

from app.application.exceptions import ValidationApplicationError
from app.domain.enums.subscription_scope import SubscriptionScope
from app.domain.models.subscription import Subscription
from app.infrastructure.persistence.repositories.event_catalog_repository import EventCatalogRepository
from app.infrastructure.persistence.repositories.map_catalog_repository import MapCatalogRepository
from app.infrastructure.persistence.repositories.subscriptions_repository import SubscriptionsRepository


@dataclass(slots=True, frozen=True)
class SubscriptionView:
    subscription_id: int | None
    scope_type: SubscriptionScope
    event_display_name: str | None
    map_display_name: str | None


class SubscriptionService:
    def __init__(
        self,
        *,
        subscriptions_repository: SubscriptionsRepository,
        event_catalog_repository: EventCatalogRepository,
        map_catalog_repository: MapCatalogRepository,
    ) -> None:
        self._subscriptions_repository = subscriptions_repository
        self._event_catalog_repository = event_catalog_repository
        self._map_catalog_repository = map_catalog_repository

    async def subscribe(
        self,
        *,
        chat_id: int,
        event_catalog_id: int | None = None,
        map_catalog_id: int | None = None,
    ) -> tuple[Subscription, bool]:
        scope_type = self._derive_scope(event_catalog_id=event_catalog_id, map_catalog_id=map_catalog_id)
        existing = await self._subscriptions_repository.get_active(
            chat_id=chat_id,
            scope_type=scope_type,
            event_catalog_id=event_catalog_id,
            map_catalog_id=map_catalog_id,
        )
        if existing is not None:
            return existing, False

        created = await self._subscriptions_repository.add(
            chat_id=chat_id,
            scope_type=scope_type,
            event_catalog_id=event_catalog_id,
            map_catalog_id=map_catalog_id,
        )
        return created, True

    async def unsubscribe(
        self,
        *,
        chat_id: int,
        event_catalog_id: int | None = None,
        map_catalog_id: int | None = None,
    ) -> int:
        scope_type = self._derive_scope(event_catalog_id=event_catalog_id, map_catalog_id=map_catalog_id)
        return await self._subscriptions_repository.disable(
            chat_id=chat_id,
            scope_type=scope_type,
            event_catalog_id=event_catalog_id,
            map_catalog_id=map_catalog_id,
        )

    async def unsubscribe_all(self, *, chat_id: int) -> int:
        return await self._subscriptions_repository.disable_all(chat_id=chat_id)

    async def unsubscribe_by_id(self, *, chat_id: int, subscription_id: int) -> int:
        return await self._subscriptions_repository.disable_by_id(
            chat_id=chat_id,
            subscription_id=subscription_id,
        )

    async def list_subscriptions(self, *, chat_id: int) -> list[SubscriptionView]:
        subscriptions = await self._subscriptions_repository.list_by_chat(chat_id=chat_id)
        events_catalog = {event.id: event.display_name for event in await self._event_catalog_repository.list_all() if event.id is not None}
        maps_catalog = {map_item.id: map_item.display_name for map_item in await self._map_catalog_repository.list_all() if map_item.id is not None}
        return [
            SubscriptionView(
                subscription_id=subscription.id,
                scope_type=subscription.scope_type,
                event_display_name=events_catalog.get(subscription.event_catalog_id),
                map_display_name=maps_catalog.get(subscription.map_catalog_id),
            )
            for subscription in subscriptions
        ]

    async def list_all_enabled(self) -> list[Subscription]:
        return await self._subscriptions_repository.list_all_enabled()

    @staticmethod
    def _derive_scope(
        *,
        event_catalog_id: int | None,
        map_catalog_id: int | None,
    ) -> SubscriptionScope:
        if event_catalog_id is None and map_catalog_id is None:
            return SubscriptionScope.ALL
        if event_catalog_id is not None and map_catalog_id is not None:
            return SubscriptionScope.EVENT_MAP
        if event_catalog_id is not None:
            return SubscriptionScope.EVENT
        if map_catalog_id is not None:
            return SubscriptionScope.MAP
        raise ValidationApplicationError("Unable to determine subscription scope")
