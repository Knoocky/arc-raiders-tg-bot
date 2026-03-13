from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.enums.subscription_scope import SubscriptionScope
from app.domain.models.scheduled_event import ScheduledEvent


@dataclass(slots=True, frozen=True)
class Subscription:
    id: int | None
    chat_id: int
    scope_type: SubscriptionScope
    event_catalog_id: int | None
    map_catalog_id: int | None
    is_enabled: bool
    created_at: datetime | None = None

    def matches(self, scheduled_event: ScheduledEvent) -> bool:
        if not self.is_enabled:
            return False
        if self.scope_type == SubscriptionScope.ALL:
            return True
        if self.scope_type == SubscriptionScope.MAP:
            return self.map_catalog_id is not None and self.map_catalog_id == scheduled_event.map_catalog_id
        if self.scope_type == SubscriptionScope.EVENT:
            return self.event_catalog_id is not None and self.event_catalog_id == scheduled_event.event_catalog_id
        if self.scope_type == SubscriptionScope.EVENT_MAP:
            return (
                self.event_catalog_id is not None
                and self.map_catalog_id is not None
                and self.event_catalog_id == scheduled_event.event_catalog_id
                and self.map_catalog_id == scheduled_event.map_catalog_id
            )
        return False

