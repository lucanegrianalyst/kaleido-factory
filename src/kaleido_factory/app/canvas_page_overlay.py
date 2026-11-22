"""Overlay grafico scollegabile per visualizzare foglio reale e slot di export sul canvas."""

from __future__ import annotations

import tkinter as tk

from kaleido_factory.app.canvas_page_space import CanvasPageSpace

GUIDE_TAG = "page_guide"


def draw_page_guide(
    canvas: tk.Canvas,
    space: CanvasPageSpace,
    *,
    show_page: bool = True,
    show_slots: bool = True,
) -> None:
    """Disegna foglio e slot sul canvas usando il tag isolato GUIDE_TAG."""
    canvas.delete(GUIDE_TAG)
    if show_page:
        pr = space.page_rect_px
        canvas.create_rectangle(
            pr.x0,
            pr.y0,
            pr.x1,
            pr.y1,
            outline="#334155",
            width=1.5,
            tags=(GUIDE_TAG,),
        )
    if show_slots:
        for sr in space.slot_rects_px:
            canvas.create_rectangle(
                sr.x0,
                sr.y0,
                sr.x1,
                sr.y1,
                outline="#0284c7",
                width=1.0,
                dash=(4, 3),
                tags=(GUIDE_TAG,),
            )
    canvas.tag_lower(GUIDE_TAG)
