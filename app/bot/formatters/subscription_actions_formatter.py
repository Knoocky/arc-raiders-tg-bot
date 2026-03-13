from __future__ import annotations


def format_watch_result(
    *,
    created: bool,
    event_display_name: str | None,
    map_display_name: str | None,
) -> str:
    if event_display_name and map_display_name:
        return (
            f"Watching {event_display_name} on {map_display_name}."
            if created
            else f"Already watching {event_display_name} on {map_display_name}."
        )
    if event_display_name:
        return f"Watching event {event_display_name}." if created else f"Already watching event {event_display_name}."
    if map_display_name:
        return f"Watching map {map_display_name}." if created else f"Already watching map {map_display_name}."
    return "Watching all events." if created else "Already watching all events."


def format_unwatch_result(
    *,
    removed: int,
    event_display_name: str | None,
    map_display_name: str | None,
) -> str:
    if event_display_name and map_display_name:
        return (
            f"Stopped watching {event_display_name} on {map_display_name}."
            if removed
            else f"No active subscription for {event_display_name} on {map_display_name}."
        )
    if event_display_name:
        return (
            f"Stopped watching event {event_display_name}."
            if removed
            else f"No active subscription for event {event_display_name}."
        )
    if map_display_name:
        return (
            f"Stopped watching map {map_display_name}."
            if removed
            else f"No active subscription for map {map_display_name}."
        )
    return "All subscriptions removed." if removed else "No active subscriptions to remove."
