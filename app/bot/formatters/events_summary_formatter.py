from __future__ import annotations

from datetime import datetime
from html import escape

from app.application.dto.event_summary_dto import EventSummaryGroupDTO, EventSummaryLineDTO, EventSummaryLineKind
from app.common.timezone import ChatTimezoneContext, format_chat_local_time
from app.common.time_utils import ensure_utc

MAX_TELEGRAM_MESSAGE_LENGTH = 4096
TRUNCATION_NOTICE = "\n\n\u2026\u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435 \u0441\u043e\u043a\u0440\u0430\u0449\u0435\u043d\u043e"


def format_events_summary(
    groups: list[EventSummaryGroupDTO],
    *,
    now: datetime,
    timezone_context: ChatTimezoneContext,
    hidden_groups_count: int = 0,
    max_length: int = MAX_TELEGRAM_MESSAGE_LENGTH,
) -> str:
    if not groups:
        return "\u041d\u0435\u0442 \u0434\u0430\u043d\u043d\u044b\u0445 \u043e \u0441\u043e\u0431\u044b\u0442\u0438\u044f\u0445."

    rendered_groups = [_format_group(group, now=now, timezone_context=timezone_context) for group in groups]
    if hidden_groups_count > 0:
        rendered_groups.append(f"...\u0438 \u0435\u0449\u0451 {hidden_groups_count} \u0433\u0440\u0443\u043f\u043f")
    return _truncate_message(rendered_groups, max_length=max_length)


def _format_group(group: EventSummaryGroupDTO, *, now: datetime, timezone_context: ChatTimezoneContext) -> str:
    lines = [f"{escape(group.event_display_name)}:"]
    if group.primary_line is None:
        lines.append("\u043d\u0435\u0442 \u0437\u0430\u043f\u043b\u0430\u043d\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u044b\u0445 \u0441\u043e\u0431\u044b\u0442\u0438\u0439")
        return "\n".join(lines)

    lines.append(_format_line(group.primary_line, now=now, is_primary=True, timezone_context=timezone_context))
    lines.extend(
        _format_line(line, now=now, is_primary=False, timezone_context=timezone_context) for line in group.future_lines
    )
    return "\n".join(lines)


def _format_line(
    line: EventSummaryLineDTO,
    *,
    now: datetime,
    is_primary: bool,
    timezone_context: ChatTimezoneContext,
) -> str:
    marker = ""
    if is_primary and line.kind is EventSummaryLineKind.ACTIVE:
        marker = "\U0001F7E2 "
    elif is_primary:
        marker = "\u23F3 "

    formatted = (
        f"{marker}{_format_time(line.starts_at, timezone_context=timezone_context)} - {escape(line.map_display_name)} - "
        f"{_format_relative_text(line, now=now)}"
    )
    if is_primary:
        return f"<b>{formatted}</b>"
    return formatted


def _format_time(value: datetime, *, timezone_context: ChatTimezoneContext) -> str:
    return format_chat_local_time(value, timezone_context=timezone_context)


def _format_relative_text(line: EventSummaryLineDTO, *, now: datetime) -> str:
    current_time = ensure_utc(now)
    if line.kind is EventSummaryLineKind.ACTIVE:
        if line.ends_at is None:
            return "\u0441\u0435\u0439\u0447\u0430\u0441"
        minutes = max(int((ensure_utc(line.ends_at) - current_time).total_seconds() // 60), 0)
        return f"\u0435\u0449\u0451 {_format_minutes(minutes)}"

    minutes = max(int((ensure_utc(line.starts_at) - current_time).total_seconds() // 60), 0)
    return f"\u0447\u0435\u0440\u0435\u0437 {_format_minutes(minutes)}"


def _format_minutes(total_minutes: int) -> str:
    if total_minutes < 60:
        return f"{total_minutes} \u043c\u0438\u043d"
    hours, minutes = divmod(total_minutes, 60)
    if minutes == 0:
        return f"{hours} \u0447"
    return f"{hours} \u0447 {minutes} \u043c\u0438\u043d"


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
        allowed_length = max(max_length - len(TRUNCATION_NOTICE), 0)
        truncated = rendered_groups[0][:allowed_length].rstrip()
        return f"{truncated}{TRUNCATION_NOTICE}"

    message = "\n\n".join(parts)
    if shortened:
        allowed_length = max_length - len(TRUNCATION_NOTICE)
        return f"{message[:allowed_length].rstrip()}{TRUNCATION_NOTICE}"
    return message
