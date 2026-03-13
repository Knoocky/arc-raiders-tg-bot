from __future__ import annotations

from enum import StrEnum


class SubscriptionScope(StrEnum):
    ALL = "all"
    MAP = "map"
    EVENT = "event"
    EVENT_MAP = "event_map"

