"""Esportatore SVG multipagina basato su PaginatedLayout e sequenze di StyledStroke."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence
from xml.sax.saxutils import escape

from kaleido_factory.core.validation import Point2D, require_finite_float, validate_points
from kaleido_factory.effects.stroke_styles import StyledStroke
from kaleido_factory.layout.pagination import PaginatedLayout


def _format_points_attr(points: Sequence[Point2D], offset_x: float, offset_y: float) -> str:
    return " ".join(f"{offset_x + p[0]:.3f},{offset_y + p[1]:.3f}" for p in points)


def render_page_svg(
    page_index: int,
    layout: PaginatedLayout,
    strokes_by_item: Sequence[Sequence[StyledStroke]],
    *,
    stroke_color: str = "#111111",
) -> str:
    """Genera il markup SVG di una singola pagina impaginata."""
    if not isinstance(layout, PaginatedLayout):
        raise TypeError("layout deve essere un'istanza di PaginatedLayout.")
    if page_index < 0 or page_index >= layout.total_pages:
        raise IndexError("page_index fuori intervallo.")
    if not isinstance(stroke_color, str) or not stroke_color.strip():
        raise ValueError("stroke_color deve essere una stringa non vuota.")

    lpage = layout.pages[page_index]
    width_pt = lpage.page.width_points
    height_pt = lpage.page.height_points
    safe_color = escape(stroke_color.strip())

    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_pt:.2f}pt" height="{height_pt:.2f}pt" viewBox="0 0 {width_pt:.2f} {height_pt:.2f}">',
        f'  <rect x="0" y="0" width="{width_pt:.2f}" height="{height_pt:.2f}" fill="#ffffff" />',
        f'  <g id="page-{page_index}">',
    ]

    for slot in lpage.slots:
        if slot.item_index < 0 or slot.item_index >= len(strokes_by_item):
            continue
        item_strokes = strokes_by_item[slot.item_index]
        lines.append(
            f'    <g id="slot-{slot.page_index}-{slot.slot_index}" transform="translate({slot.x_pt:.3f},{slot.y_pt:.3f})">'
        )
        for st in item_strokes:
            if not isinstance(st, StyledStroke):
                continue
            pts = validate_points(st.points, min_points=0, allow_degenerate=True)
            if len(pts) < 2:
                continue
            w = require_finite_float(st.width, "stroke.width", positive_only=True)
            op = require_finite_float(st.opacity, "stroke.opacity", allow_zero=True)
            op_clamped = max(0.0, min(1.0, op))
            pts_str = _format_points_attr(pts, 0.0, 0.0)
            lines.append(
                f'      <polyline fill="none" stroke="{safe_color}" stroke-width="{w:.3f}" stroke-opacity="{op_clamped:.3f}" points="{pts_str}" />'
            )
        lines.append("    </g>")

    lines.append("  </g>")
    lines.append("</svg>")
    return "\n".join(lines)


def export_layout_svg(
    layout: PaginatedLayout,
    strokes_by_item: Sequence[Sequence[StyledStroke]],
    output_dir: Path | str,
    *,
    prefix: str = "page",
    stroke_color: str = "#111111",
) -> list[Path]:
    """Esporta tutte le pagine di un PaginatedLayout come file SVG UTF-8 senza BOM."""
    if not isinstance(layout, PaginatedLayout):
        raise TypeError("layout deve essere un'istanza di PaginatedLayout.")
    if not isinstance(prefix, str) or not prefix.strip():
        raise ValueError("prefix deve essere una stringa non vuota.")

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for idx in range(layout.total_pages):
        svg_text = render_page_svg(idx, layout, strokes_by_item, stroke_color=stroke_color)
        target = out_path / f"{prefix.strip()}_{idx + 1:03d}.svg"
        target.write_text(svg_text, encoding="utf-8")
        written.append(target)

    return written