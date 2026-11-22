"""Test per il modulo scollegabile della guida pagina/slot sul canvas."""

from __future__ import annotations

from kaleido_factory.app.canvas_commands import parse_command
from kaleido_factory.app.canvas_page_overlay import compute_page_guide_layout
from kaleido_factory.app.pipeline import CompositionConfig
from kaleido_factory.core.document import MarginsSpec
from kaleido_factory.layout.formats import make_book_page


def test_compute_page_guide_layout_scales_and_centers_slots() -> None:
    page = make_book_page("book_6x9", orientation="portrait", margins=MarginsSpec(36, 36, 36, 36))
    guide = compute_page_guide_layout(
        page,
        canvas_width=920.0,
        canvas_height=564.0,
        rows=2,
        cols=2,
        gutter_pt=12.0,
    )
    assert guide.scale_pt_to_px > 0.0
    assert guide.page_rect.x0 >= 28.0
    assert guide.page_rect.y0 >= 28.0
    assert guide.page_rect.x1 <= 920.0 - 28.0
    assert guide.page_rect.y1 <= 564.0 - 28.0
    assert len(guide.slot_rects) == 4
    for sr in guide.slot_rects:
        assert sr.x0 >= guide.page_rect.x0
        assert sr.y0 >= guide.page_rect.y0
        assert sr.x1 <= guide.page_rect.x1
        assert sr.y1 <= guide.page_rect.y1


def test_guide_command_toggles_visibility_action() -> None:
    cfg = CompositionConfig()
    _, msg_off, spec_off = parse_command("guide off", cfg)
    _, msg_on, spec_on = parse_command("guide on", cfg)
    assert "nascosta" in msg_off and spec_off == "set_guide:0"
    assert "visibile" in msg_on and spec_on == "set_guide:1"
