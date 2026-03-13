from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Generic, Sequence, TypeVar

T = TypeVar("T")


@dataclass(slots=True, frozen=True)
class PageSlice(Generic[T]):
    items: tuple[T, ...]
    page: int
    total_pages: int

    @property
    def has_previous(self) -> bool:
        return self.page > 0

    @property
    def has_next(self) -> bool:
        return self.page + 1 < self.total_pages


def paginate_items(items: Sequence[T], *, page: int, page_size: int) -> PageSlice[T]:
    safe_page_size = max(page_size, 1)
    total_pages = max(ceil(len(items) / safe_page_size), 1)
    safe_page = min(max(page, 0), total_pages - 1)
    start = safe_page * safe_page_size
    end = start + safe_page_size
    return PageSlice(
        items=tuple(items[start:end]),
        page=safe_page,
        total_pages=total_pages,
    )
