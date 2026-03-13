from datetime import UTC, datetime

from app.application.services.notification_service import NotificationService


def test_notification_window_matches_within_scheduler_minute() -> None:
    starts_at = datetime(2026, 3, 11, 15, 0, tzinfo=UTC)
    now = datetime(2026, 3, 11, 14, 30, 30, tzinfo=UTC)

    assert NotificationService.should_send_notification(starts_at, now=now, minutes_before=30) is True


def test_notification_window_skips_outside_offset_window() -> None:
    starts_at = datetime(2026, 3, 11, 15, 0, tzinfo=UTC)
    now = datetime(2026, 3, 11, 14, 28, 59, tzinfo=UTC)

    assert NotificationService.should_send_notification(starts_at, now=now, minutes_before=30) is False

