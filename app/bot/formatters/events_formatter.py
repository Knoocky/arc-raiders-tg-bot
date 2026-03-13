from __future__ import annotations

from datetime import datetime

from app.application.dto.event_summary_dto import EventSummaryGroupDTO, EventSummaryLineDTO, EventSummaryLineKind
from app.common.time_utils import ensure_utc

MAX_TELEGRAM_MESSAGE_LENGTH = 4096
TRUNCATION_NOTICE = "\n\n\u2026\u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435 \u0441\u043e\u043a\u0440\u0430\u0449\u0435\u043d\u043e"


def format_events_summary(
    groups: list[EventSummaryGroupDTO],
    *,
    now: datetime,
    hidden_groups_count: int = 0,
    max_length: int = MAX_TELEGRAM_MESSAGE_LENGTH,
) -> str:
    if not groups:
        return "\u041d\u0435\u0442 \u0434\u0430\u043d\u043d\u044b\u0445 \u043e \u0441\u043e\u0431\u044b\u0442\u0438\u044f\u0445."

    rendered_groups = [_format_group(group, now=now) for group in groups]
    if hidden_groups_count > 0:
        rendered_groups.append(f"...и ещё {hidden_groups_count} групп")
    return _truncate_message(rendered_groups, max_length=max_length)


def _format_group(group: EventSummaryGroupDTO, *, now: datetime) -> str:
    lines = [f"{group.event_display_name}:"]
    if group.primary_line is None:
        lines.append("нет запланированных событий")
        return "\n".join(lines)

    lines.append(_format_line(group.primary_line, now=now, is_primary=True))
    lines.extend(_format_line(line, now=now, is_primary=False) for line in group.future_lines)
    return "\n".join(lines)


def _format_line(line: EventSummaryLineDTO, *, now: datetime, is_primary: bool) -> str:
    prefix = ""
    suffix = ""
    if is_primary and line.kind is EventSummaryLineKind.ACTIVE:
        prefix = "**"
        suffix = "**"

    marker = ""
    if is_primary and line.kind is EventSummaryLineKind.ACTIVE:
        marker = "🟢 "
    elif is_primary:
        marker = "⏳ "

    return f"{prefix}{marker}{_format_time(line.starts_at)} - {line.map_display_name} - {_format_relative_text(line, now=now)}{suffix}"


def _format_time(value: datetime) -> str:
    return ensure_utc(value).strftime("%H:%M UTC")


def _format_relative_text(line: EventSummaryLineDTO, *, now: datetime) -> str:
    current_time = ensure_utc(now)
    if line.kind is EventSummaryLineKind.ACTIVE:
        if line.ends_at is None:
            return "сейчас"
        minutes = max(int((ensure_utc(line.ends_at) - current_time).total_seconds() // 60), 0)
        return f"ещё {_format_minutes(minutes)}"

    minutes = max(int((ensure_utc(line.starts_at) - current_time).total_seconds() // 60), 0)
    return f"через {_format_minutes(minutes)}"


def _format_minutes(total_minutes: int) -> str:
    if total_minutes < 60:
        return f"{total_minutes} мин"
    hours, minutes = divmod(total_minutes, 60)
    if minutes == 0:
        return f"{hours} ч"
    return f"{hours} ч {minutes} мин"


def _truncate_message(rendered_groups: list[str], *, max_length: int) -> str:
    parts: list[str] = []
    shortened = False
    for group_text in rendered_groups:
        candidate_parts = [*parts, group_text]
        candidate = "\n\n".join(candidate_parts)
        if len(candidate) <= max_length:
            parts = candidate_parts
            continue
        shortened = True
        break

    if not parts:
        truncated = rendered_groups[0][: max_length - len("\n…сообщение сокращено")].rstrip()
        return f"{truncated}\n…сообщение сокращено"

    message = "\n\n".join(parts)
    if shortened:
        notice = "\n\n…сообщение сокращено"
        allowed_length = max_length - len(notice)
        return f"{message[:allowed_length].rstrip()}{notice}"
    return message
