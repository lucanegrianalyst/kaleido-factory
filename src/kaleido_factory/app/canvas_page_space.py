"""Mappatura geometrica bidirezionale tra coordinate del canvas e coordinate reali di pagina/slot."""

from __future__ import annotations

from dataclasses import dataclass

from kaleido_factory.core.document import PageSpec
from kaleido_factory.core.validation import Point2D
from kaleido_factory.layout.pagination import PlacedSlot, paginate_items


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
class CanvasPageSpace:
    """Spazio condiviso tra anteprima canvas e coordinate reali in punti (pt) dell'export."""

    page_rect_px: CanvasRect
    slot_rects_px: tuple[CanvasRect, ...]
    slots_pt: tuple[PlacedSlot, ...]
    scale_pt_to_px: float

    @property
    def scale_px_to_pt(self) -> float:
        return 1.0 / self.scale_pt_to_px if self.scale_pt_to_px > 0 else 1.0

    def canvas_to_page_pt(self, pt: Point2D) -> Point2D:
        """Converte un punto dal canvas (px) a coordinate assolute di pagina (pt)."""
        inv = self.scale_px_to_pt
        return ((pt[0] - self.page_rect_px.x0) * inv, (pt[1] - self.page_rect_px.y0) * inv)

    def page_pt_to_canvas(self, pt: Point2D) -> Point2D:
        """Converte un punto da coordinate assolute di pagina (pt) a coordinate canvas (px)."""
        s = self.scale_pt_to_px
        return (self.page_rect_px.x0 + pt[0] * s, self.page_rect_px.y0 + pt[1] * s)

    def canvas_points_to_slot_local_pt(
        self,
        points: list[Point2D] | tuple[Point2D, ...],
        slot_index: int = 0,
    ) -> list[Point2D]:
        """Converte una polilinea dal canvas (px) a coordinate locali dello slot di destinazione (pt)."""
        slot = self.slots_pt[slot_index] if 0 <= slot_index < len(self.slots_pt) else None
        ox_pt = slot.x_pt if slot is not None else 0.0
        oy_pt = slot.y_pt if slot is not None else 0.0
        return [
            (px_pt - ox_pt, py_pt - oy_pt)
            for px_pt, py_pt in (self.canvas_to_page_pt(p) for p in points)
        ]

    def slot_local_pt_to_canvas(self, pt: Point2D, slot_index: int = 0) -> Point2D:
        """Converte un punto locale dello slot (pt) in coordinate del canvas (px)."""
        slot = self.slots_pt[slot_index] if 0 <= slot_index < len(self.slots_pt) else None
        ox_pt = slot.x_pt if slot is not None else 0.0
        oy_pt = slot.y_pt if slot is not None else 0.0
        return self.page_pt_to_canvas((ox_pt + pt[0], oy_pt + pt[1]))


def build_canvas_page_space(
    page: PageSpec,
    *,
    canvas_width: float,
    canvas_height: float,
    rows: int = 1,
    cols: int = 1,
    gutter_pt: float = 12.0,
    outer_margin_px: float = 24.0,
) -> CanvasPageSpace:
    """Costruisce la mappatura pagina/slot per qualunque formato e griglia."""
    avail_w = max(40.0, canvas_width - 2.0 * outer_margin_px)
    avail_h = max(40.0, canvas_height - 2.0 * outer_margin_px)
    page_w_pt = max(1.0, float(page.width_points))
    page_h_pt = max(1.0, float(page.height_points))

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
    return CanvasPageSpace(
        page_rect_px=page_rect,
        slot_rects_px=slot_rects,
        slots_pt=slots,
        scale_pt_to_px=scale,
    )
