"""Guida visiva opzionale della pagina e degli slot di export sul canvas."""

from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk

from kaleido_factory.core.document import PageSpec
from kaleido_factory.layout.pagination import paginate_items

GUIDE_TAG = "page_guide"


@dataclass(frozen=True)
class CanvasRect:
    """Rettangolo in coordinate del canvas (pixel)."""

    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return max(0.0, self.x1 - self.x0)

    @property
    def height(self) -> float:
        return max(0.0, self.y1 - self.y0)


@dataclass(frozen=True)
class PageGuideLayout:
    """Rettangoli scalati di pagina e slot per l'anteprima sul canvas."""

    page_rect: CanvasRect
    slot_rects: tuple[CanvasRect, ...]
    scale_pt_to_px: float


def compute_page_guide_layout(
    page: PageSpec,
    *,
    canvas_width: float,
    canvas_height: float,
    rows: int = 1,
    cols: int = 1,
    gutter_pt: float = 12.0,
    outer_margin_px: float = 28.0,
) -> PageGuideLayout:
    """Calcola pagina e slot in scala reale dentro l'area disponibile del canvas."""
    avail_w = max(40.0, canvas_width - 2.0 * outer_margin_px)
    avail_h = max(40.0, canvas_height - 2.0 * outer_margin_px)
    page_w_pt = max(1.0, float(page.width_inches) * 72.0)
    page_h_pt = max(1.0, float(page.height_inches) * 72.0)

    scale = min(avail_w / page_w_pt, avail_h / page_h_pt)
    scaled_w = page_w_pt * scale
    scaled_h = page_h_pt * scale

    ox = (canvas_width - scaled_w) * 0.5
    oy = (canvas_height - scaled_h) * 0.5
    page_rect = CanvasRect(x0=ox, y0=oy, x1=ox + scaled_w, y1=oy + scaled_h)

    item_count = max(1, rows * cols)
    paginated = paginate_items(
        item_count,
        page=page,
        rows=rows,
        cols=cols,
        gutter_pt=gutter_pt,
    )
    slots = paginated.pages[0].slots if paginated.pages else ()
    slot_rects = tuple(
        CanvasRect(
            x0=ox + s.x_pt * scale,
            y0=oy + s.y_pt * scale,
            x1=ox + (s.x_pt + s.width_pt) * scale,
            y1=oy + (s.y_pt + s.height_pt) * scale,
        )
        for s in slots
    )
    return PageGuideLayout(page_rect=page_rect, slot_rects=slot_rects, scale_pt_to_px=scale)


def draw_page_guide(
    canvas: tk.Canvas,
    guide: PageGuideLayout,
    *,
    show_page: bool = True,
    show_slots: bool = True,
) -> None:
    """Disegna pagina e slot sul canvas usando un tag dedicato e scollegabile."""
    canvas.delete(GUIDE_TAG)
    if show_page:
        pr = guide.page_rect
        canvas.create_rectangle(
            pr.x0,
            pr.y0,
            pr.x1,
            pr.y1,
            outline="#7a8b99",
            width=1.5,
            dash=(6, 4),
            tags=(GUIDE_TAG,),
        )
    if show_slots:
        for sr in guide.slot_rects:
            canvas.create_rectangle(
                sr.x0,
                sr.y0,
                sr.x1,
                sr.y1,
                outline="#2b7a9b",
                width=1.0,
                dash=(3, 3),
                tags=(GUIDE_TAG,),
            )
    canvas.tag_lower(GUIDE_TAG)
