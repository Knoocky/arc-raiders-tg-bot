from __future__ import annotations

from dataclasses import dataclass

MENU_CALLBACK_PREFIX = "m"


class MenuAction:
    ROOT = "rt"
    SUBSCRIBE_EVENTS = "sb"
    SUBSCRIBE_MAPS = "sg"
    SUBSCRIBE_ANY_MAP = "sa"
    SUBSCRIBE_MAP = "sc"
    UNSUBSCRIBE_LIST = "ub"
    UNSUBSCRIBE_ONE = "ud"
    UNSUBSCRIBE_ALL = "ua"
    NOTIFICATIONS = "nb"
    NOTIFICATION_ADD = "na"
    NOTIFICATION_REMOVE = "nr"
    NOTIFICATION_CLEAR = "nc"
    NOTIFICATION_CUSTOM = "nx"
    SCHEDULE_ALL = "ev"
    SCHEDULE_EVENTS = "ep"
    SCHEDULE_EVENT = "ee"
    LIST = "ls"
    HELP = "hp"


@dataclass(slots=True, frozen=True)
class MenuCallback:
    action: str
    parts: tuple[str, ...]


def build_menu_callback(action: str, *parts: int | str) -> str:
    return ":".join([MENU_CALLBACK_PREFIX, action, *(str(part) for part in parts)])


def parse_menu_callback(data: str | None) -> MenuCallback | None:
    if not data:
        return None
    parts = tuple(part for part in data.split(":") if part != "")
    if len(parts) < 2 or parts[0] != MENU_CALLBACK_PREFIX:
        return None
    return MenuCallback(action=parts[1], parts=parts[2:])
