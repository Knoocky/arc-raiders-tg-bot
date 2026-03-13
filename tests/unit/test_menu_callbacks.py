from __future__ import annotations

from app.bot.menu.callbacks import MenuAction, build_menu_callback, parse_menu_callback


def test_build_and_parse_menu_callback_round_trip() -> None:
    callback_data = build_menu_callback(MenuAction.SUBSCRIBE_MAP, 12, 34, 1, 2)

    parsed = parse_menu_callback(callback_data)

    assert parsed is not None
    assert parsed.action == MenuAction.SUBSCRIBE_MAP
    assert parsed.parts == ("12", "34", "1", "2")


def test_parse_menu_callback_rejects_unrelated_payload() -> None:
    assert parse_menu_callback("watch:meteor") is None
    assert parse_menu_callback(None) is None
