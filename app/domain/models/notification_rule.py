from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class NotificationRule:
    chat_id: int
    minutes_before: int
