from __future__ import annotations

import re
import unicodedata

_SEPARATORS_RE = re.compile(r"[-_/]+")
_PUNCTUATION_RE = re.compile(r"[^\w\s]")
_SPACES_RE = re.compile(r"\s+")


def normalize_lookup_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    normalized = _SEPARATORS_RE.sub(" ", normalized)
    normalized = _PUNCTUATION_RE.sub(" ", normalized)
    return _SPACES_RE.sub(" ", normalized).strip()

