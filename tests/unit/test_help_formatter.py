from __future__ import annotations

from app.bot.formatters.help_formatter import build_help_text


def test_help_formatter_returns_plain_text_with_command_placeholders() -> None:
    text = build_help_text()

    assert "/menu - open the interactive inline menu" in text
    assert "/events map <map name>" in text
    assert "/watch event <event name> | map <map name>" in text
    assert "separate them with `|`" in text
