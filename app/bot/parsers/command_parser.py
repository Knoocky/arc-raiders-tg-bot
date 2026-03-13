from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.application.exceptions import ValidationApplicationError


@dataclass(slots=True, frozen=True)
class ParsedEventsCommand:
    event_name: str | None = None
    map_name: str | None = None


@dataclass(slots=True, frozen=True)
class ParsedSubscriptionCommand:
    is_all: bool = False
    event_name: str | None = None
    map_name: str | None = None


@dataclass(slots=True, frozen=True)
class ParsedNotifyCommand:
    action: Literal["replace", "add", "remove", "list"]
    minutes: tuple[int, ...] = ()


def parse_events_command(raw_args: str | None) -> ParsedEventsCommand:
    args = (raw_args or "").strip()
    if not args:
        return ParsedEventsCommand()
    if "|" in args:
        raise ValidationApplicationError("The /events command supports only one filter at a time.")
    _ensure_no_missing_separator(args)

    lowered = args.casefold()
    if lowered.startswith("map "):
        map_name = args[4:].strip()
        _ensure_non_empty_value(map_name, "map")
        return ParsedEventsCommand(map_name=map_name)
    if lowered.startswith("event "):
        event_name = args[6:].strip()
        _ensure_non_empty_value(event_name, "event")
        return ParsedEventsCommand(event_name=event_name)
    raise ValidationApplicationError("Usage: /events, /events map <map name>, /events event <event name>.")


def parse_subscription_command(raw_args: str | None) -> ParsedSubscriptionCommand:
    args = (raw_args or "").strip()
    if not args:
        raise ValidationApplicationError("Usage: /watch all | map <name> | event <name> | event <name> | map <name>.")
    if args.casefold() == "all":
        return ParsedSubscriptionCommand(is_all=True)

    if "|" not in args:
        _ensure_no_missing_separator(args)
        if args.casefold().startswith("map "):
            map_name = args[4:].strip()
            _ensure_non_empty_value(map_name, "map")
            return ParsedSubscriptionCommand(map_name=map_name)
        if args.casefold().startswith("event "):
            event_name = args[6:].strip()
            _ensure_non_empty_value(event_name, "event")
            return ParsedSubscriptionCommand(event_name=event_name)
        raise ValidationApplicationError("Unsupported subscription syntax.")

    parts = [part.strip() for part in args.split("|")]
    if len(parts) != 2 or not all(parts):
        raise ValidationApplicationError("Combined event + map syntax must use exactly one `|` separator.")

    event_name: str | None = None
    map_name: str | None = None
    for part in parts:
        lowered = part.casefold()
        if lowered.startswith("event "):
            if event_name is not None:
                raise ValidationApplicationError("Event is specified more than once.")
            event_name = part[6:].strip()
            _ensure_non_empty_value(event_name, "event")
            continue
        if lowered.startswith("map "):
            if map_name is not None:
                raise ValidationApplicationError("Map is specified more than once.")
            map_name = part[4:].strip()
            _ensure_non_empty_value(map_name, "map")
            continue
        raise ValidationApplicationError("Combined command must contain `event <name>` and `map <name>` parts.")

    if event_name is None or map_name is None:
        raise ValidationApplicationError("Combined command must contain both `event` and `map` parts.")
    return ParsedSubscriptionCommand(event_name=event_name, map_name=map_name)


def parse_notify_command(raw_args: str | None) -> ParsedNotifyCommand:
    args = (raw_args or "").strip()
    if not args:
        raise ValidationApplicationError("Usage: /notify <minutes...> | add <minutes...> | remove <minutes...> | list.")

    parts = args.split()
    action = parts[0].casefold()
    if action == "list":
        if len(parts) != 1:
            raise ValidationApplicationError("Usage: /notify list")
        return ParsedNotifyCommand(action="list")
    if action in {"add", "remove"}:
        minutes = _parse_minutes(parts[1:])
        return ParsedNotifyCommand(action=action, minutes=minutes)
    minutes = _parse_minutes(parts)
    return ParsedNotifyCommand(action="replace", minutes=minutes)


def _parse_minutes(values: list[str]) -> tuple[int, ...]:
    if not values:
        raise ValidationApplicationError("Provide at least one positive minute value.")
    minutes: set[int] = set()
    for value in values:
        try:
            minute = int(value)
        except ValueError as exc:
            raise ValidationApplicationError(f"Invalid minute value: {value}") from exc
        if minute <= 0:
            raise ValidationApplicationError("Minutes must be positive integers.")
        minutes.add(minute)
    return tuple(sorted(minutes, reverse=True))


def _ensure_no_missing_separator(args: str) -> None:
    lowered = args.casefold()
    if lowered.startswith("event ") and " map " in lowered:
        raise ValidationApplicationError("Use `|` between the `event` and `map` parts.")
    if lowered.startswith("map ") and " event " in lowered:
        raise ValidationApplicationError("Use `|` between the `event` and `map` parts.")


def _ensure_non_empty_value(value: str, label: str) -> None:
    if not value:
        raise ValidationApplicationError(f"Provide a {label} name.")
