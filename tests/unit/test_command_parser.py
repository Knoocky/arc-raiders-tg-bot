import pytest

from app.application.exceptions import ValidationApplicationError
from app.bot.parsers.command_parser import (
    parse_events_command,
    parse_notify_command,
    parse_subscription_command,
)


def test_parse_events_command_by_map() -> None:
    parsed = parse_events_command("map Space port")
    assert parsed.map_name == "Space port"
    assert parsed.event_name is None


def test_parse_subscription_command_combined() -> None:
    parsed = parse_subscription_command("event Meteor shower | map Blue gate")
    assert parsed.event_name == "Meteor shower"
    assert parsed.map_name == "Blue gate"


def test_parse_subscription_command_requires_separator_for_combined_input() -> None:
    with pytest.raises(ValidationApplicationError):
        parse_subscription_command("event Meteor shower map Blue gate")


def test_parse_notify_command_replace() -> None:
    parsed = parse_notify_command("30 15 5")
    assert parsed.action == "replace"
    assert parsed.minutes == (30, 15, 5)


def test_parse_notify_command_list() -> None:
    parsed = parse_notify_command("list")
    assert parsed.action == "list"
    assert parsed.minutes == ()

