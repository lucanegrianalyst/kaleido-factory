"""Test per layout/formats.py e layout/pagination.py."""

from __future__ import annotations

import pytest

from kaleido_factory.core.document import MarginsSpec
from kaleido_factory.layout.formats import compute_printable_rect, make_book_page
from kaleido_factory.layout.pagination import paginate_items


def test_book_presets_orientations_and_printable_area() -> None:
    p_port = make_book_page("book_6x9", orientation="portrait", margins=MarginsSpec(36, 36, 36, 36))
    assert p_port.width_points == pytest.approx(6.0 * 72.0)
    assert p_port.height_points == pytest.approx(9.0 * 72.0)

    rect = compute_printable_rect(p_port)
    assert rect.x_pt == pytest.approx(36.0)
    assert rect.width_pt == pytest.approx(6.0 * 72.0 - 72.0)

    p_land = make_book_page("book_6x9", orientation="landscape", margins=MarginsSpec(36, 36, 36, 36))
    assert p_land.width_points == pytest.approx(9.0 * 72.0)
    assert p_land.height_points == pytest.approx(6.0 * 72.0)


def test_pagination_multi_page_and_aspect_fit() -> None:
    page = make_book_page("book_square_85", orientation="square", margins=MarginsSpec(36, 36, 36, 36))
    layout = paginate_items(
        5,
        page=page,
        rows=2,
        cols=2,
        gutter_pt=12.0,
        preserve_aspect=True,
        item_aspect_ratios=[2.0, 1.0, 1.0, 1.0, 0.5],
    )
    assert layout.total_pages == 2
    assert len(layout.pages[0].slots) == 4
    assert len(layout.pages[1].slots) == 1
    assert layout.pages[1].slots[0].item_index == 4

    # Primo slot con aspect ratio 2.0 in cella quadrata deve avere altezza dimezzata rispetto alla larghezza.
    s0 = layout.pages[0].slots[0]
    assert s0.width_pt == pytest.approx(s0.height_pt * 2.0)