from datetime import UTC, datetime

from app.domain.enums.subscription_scope import SubscriptionScope
from app.domain.models.scheduled_event import ScheduledEvent
from app.domain.models.subscription import Subscription


def test_subscription_matches_all_scope() -> None:
    event = ScheduledEvent(
        id=1,
        source_id="source",
        event_catalog_id=10,
        map_catalog_id=20,
        event_display_name="Meteor Shower",
        map_display_name="Blue Gate",
        starts_at=datetime(2026, 3, 11, 12, 0, tzinfo=UTC),
    )
    subscription = Subscription(
        id=1,
        chat_id=100,
        scope_type=SubscriptionScope.ALL,
        event_catalog_id=None,
        map_catalog_id=None,
        is_enabled=True,
    )

    assert subscription.matches(event) is True


def test_subscription_matches_event_map_scope() -> None:
    event = ScheduledEvent(
        id=1,
        source_id="source",
        event_catalog_id=10,
        map_catalog_id=20,
        event_display_name="Meteor Shower",
        map_display_name="Blue Gate",
        starts_at=datetime(2026, 3, 11, 12, 0, tzinfo=UTC),
    )
    subscription = Subscription(
        id=1,
        chat_id=100,
        scope_type=SubscriptionScope.EVENT_MAP,
        event_catalog_id=10,
        map_catalog_id=20,
        is_enabled=True,
    )

    assert subscription.matches(event) is True


def test_subscription_does_not_match_different_map() -> None:
    event = ScheduledEvent(
        id=1,
        source_id="source",
        event_catalog_id=10,
        map_catalog_id=20,
        event_display_name="Meteor Shower",
        map_display_name="Blue Gate",
        starts_at=datetime(2026, 3, 11, 12, 0, tzinfo=UTC),
    )
    subscription = Subscription(
        id=1,
        chat_id=100,
        scope_type=SubscriptionScope.MAP,
        event_catalog_id=None,
        map_catalog_id=999,
        is_enabled=True,
    )

    assert subscription.matches(event) is False

