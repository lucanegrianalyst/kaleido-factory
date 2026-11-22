"""Test per CanvasPageSpace e conversione coordinate senza rimpicciolimento."""

from __future__ import annotations

from kaleido_factory.app.canvas_page_space import build_canvas_page_space
from kaleido_factory.core.document import MarginsSpec
from kaleido_factory.layout.formats import make_book_page


def test_canvas_to_slot_local_preserves_relative_dimensions() -> None:
    page = make_book_page("book_6x9", orientation="portrait", margins=MarginsSpec(36, 36, 36, 36))
    space = build_canvas_page_space(page, canvas_width=920.0, canvas_height=564.0, rows=1, cols=1)

    p_c0 = space.slot_local_pt_to_canvas((10.0, 20.0), slot_index=0)
    p_c1 = space.slot_local_pt_to_canvas((110.0, 20.0), slot_index=0)
    roundtrip = space.canvas_points_to_slot_local_pt([p_c0, p_c1], slot_index=0)

    assert abs((roundtrip[1][0] - roundtrip[0][0]) - 100.0) < 1e-6
    assert abs((roundtrip[1][1] - roundtrip[0][1]) - 0.0) < 1e-6
