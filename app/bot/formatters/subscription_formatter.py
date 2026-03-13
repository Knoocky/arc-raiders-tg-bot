from __future__ import annotations

from app.application.services.subscription_service import SubscriptionView
from app.domain.enums.subscription_scope import SubscriptionScope


def format_subscriptions(subscriptions: list[SubscriptionView]) -> str:
    if not subscriptions:
        return "No active subscriptions."

    lines = ["Subscriptions:"]
    for subscription in subscriptions:
        lines.append(f"- {format_subscription_scope(subscription)}")
    return "\n".join(lines)


def format_subscription_scope(subscription: SubscriptionView) -> str:
    if subscription.scope_type == SubscriptionScope.ALL:
        return "all events"
    if subscription.scope_type == SubscriptionScope.MAP:
        return f"map: {subscription.map_display_name}"
    if subscription.scope_type == SubscriptionScope.EVENT:
        return f"event: {subscription.event_display_name}"
    return f"event: {subscription.event_display_name} | map: {subscription.map_display_name}"

