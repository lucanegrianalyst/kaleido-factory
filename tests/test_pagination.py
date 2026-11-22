from __future__ import annotations

from kaleido_factory.layout.formats import make_book_page
from kaleido_factory.layout.pagination import compute_printable_rect, paginate_items


def test_printable_rect_valid_bounds() -> None:
    page = make_book_page("book_a4", orientation="portrait")
    rect = compute_printable_rect(page)
    assert rect.x_pt >= 0.0
    assert rect.y_pt >= 0.0
    assert rect.width_pt > 0.0
    assert rect.height_pt > 0.0


def test_paginate_items_multiple_pages() -> None:
    page = make_book_page("book_a4", orientation="portrait")
    layout = paginate_items(5, page=page, rows=2, cols=2, gutter_pt=10.0)
    assert len(layout.pages) == 2
    assert len(layout.pages[0].slots) == 4
    assert len(layout.pages[1].slots) == 1
