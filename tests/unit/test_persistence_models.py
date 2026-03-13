from __future__ import annotations

from app.infrastructure.persistence.models import SubscriptionModel


def test_subscription_scope_enum_uses_database_values() -> None:
    enum_type = SubscriptionModel.__table__.c.scope_type.type

    assert enum_type.enums == ["all", "map", "event", "event_map"]
