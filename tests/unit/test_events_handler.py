from __future__ import annotations

from app.bot.handlers.events import _full_schedule_future_lines_limit


def test_full_schedule_uses_compact_group_limit() -> None:
    assert _full_schedule_future_lines_limit(event_catalog_id=None, map_catalog_id=None) == 1


def test_filtered_schedule_keeps_default_group_detail() -> None:
    assert _full_schedule_future_lines_limit(event_catalog_id=1, map_catalog_id=None) is None
    assert _full_schedule_future_lines_limit(event_catalog_id=None, map_catalog_id=1) is None
    assert _full_schedule_future_lines_limit(event_catalog_id=1, map_catalog_id=2) is None
