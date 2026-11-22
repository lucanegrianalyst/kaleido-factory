"""Test per overlay pagina/slot scollegabile e mappatura CanvasPageSpace."""

from __future__ import annotations

from kaleido_factory.app.canvas_commands import parse_command
from kaleido_factory.app.canvas_page_overlay import GUIDE_TAG, draw_page_guide
from kaleido_factory.app.canvas_page_space import build_canvas_page_space
from kaleido_factory.app.pipeline import CompositionConfig
from kaleido_factory.core.document import MarginsSpec
from kaleido_factory.layout.formats import make_book_page


class _FakeCanvas:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def delete(self, tag: str) -> None:
        self.calls.append(("delete", (tag,), {}))

    def create_rectangle(self, *coords: float, **kwargs: object) -> int:
        self.calls.append(("create_rectangle", coords, kwargs))
        return len(self.calls)

    def tag_lower(self, tag: str) -> None:
        self.calls.append(("tag_lower", (tag,), {}))


def test_build_canvas_page_space_centers_page_and_slots() -> None:
    page = make_book_page("book_6x9", orientation="portrait", margins=MarginsSpec(36, 36, 36, 36))
    space = build_canvas_page_space(
        page,
        canvas_width=920.0,
        canvas_height=564.0,
        rows=2,
        cols=2,
        gutter_pt=12.0,
    )
    assert space.scale_pt_to_px > 0.0
    assert space.page_rect_px.x0 >= 24.0
    assert space.page_rect_px.y0 >= 24.0
    assert space.page_rect_px.x1 <= 920.0 - 24.0
    assert space.page_rect_px.y1 <= 564.0 - 24.0
    assert len(space.slot_rects_px) == 4
    for sr in space.slot_rects_px:
        assert sr.x0 >= space.page_rect_px.x0
        assert sr.y0 >= space.page_rect_px.y0
        assert sr.x1 <= space.page_rect_px.x1
        assert sr.y1 <= space.page_rect_px.y1


def test_draw_page_guide_uses_isolated_tag() -> None:
    page = make_book_page("book_6x9", orientation="portrait", margins=MarginsSpec(36, 36, 36, 36))
    space = build_canvas_page_space(page, canvas_width=920.0, canvas_height=564.0, rows=1, cols=1)
    fake = _FakeCanvas()
    draw_page_guide(fake, space, show_page=True, show_slots=True)
    assert fake.calls[0] == ("delete", (GUIDE_TAG,), {})
    rect_calls = [c for c in fake.calls if c[0] == "create_rectangle"]
    assert len(rect_calls) == 2
    assert all(c[2].get("tags") == (GUIDE_TAG,) for c in rect_calls)


def test_guide_command_toggles_visibility_action() -> None:
    cfg = CompositionConfig()
    _, msg_off, spec_off = parse_command("guide off", cfg)
    _, msg_on, spec_on = parse_command("guide on", cfg)
    assert "nascosta" in msg_off and spec_off == "set_guide:0"
    assert "visibile" in msg_on and spec_on == "set_guide:1"
