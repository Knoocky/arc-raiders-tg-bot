from app.common.text_normalizer import normalize_lookup_text


def test_normalize_lookup_text_collapses_spaces_and_case() -> None:
    assert normalize_lookup_text("  Meteor   Shower  ") == "meteor shower"


def test_normalize_lookup_text_replaces_safe_separators() -> None:
    assert normalize_lookup_text("SPACE-PORT") == "space port"


def test_normalize_lookup_text_strips_punctuation() -> None:
    assert normalize_lookup_text("Blue, Gate!") == "blue gate"

