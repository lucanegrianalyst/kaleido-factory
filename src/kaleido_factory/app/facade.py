"""Facciata applicativa per comporre, impaginare ed esportare composizioni kaleidoscopiche."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Sequence

from kaleido_factory.app.pipeline import CompositionConfig, build_styled_strokes
from kaleido_factory.core.cache import ParameterCache
from kaleido_factory.core.document import MarginsSpec, PageSpec
from kaleido_factory.core.point_budget import BudgetConfig
from kaleido_factory.core.validation import Point2D
from kaleido_factory.effects.stroke_styles import StyledStroke
from kaleido_factory.layout.formats import make_book_page
from kaleido_factory.layout.pagination import PaginatedLayout, paginate_items
from kaleido_factory.rendering.raster_pdf_exporter import export_layout_pdf, export_layout_png
from kaleido_factory.rendering.svg_exporter import export_layout_svg


@dataclass(frozen=True)
class ExportBundle:
    """Riepilogo dei file esportati per un documento impaginato."""

    layout: PaginatedLayout
    svg_files: tuple[Path, ...]
    png_files: tuple[Path, ...]
    pdf_file: Path | None


def _fit_strokes_to_slot(
    strokes: tuple[StyledStroke, ...],
    width_pt: float,
    height_pt: float,
    pad_ratio: float = 0.9,
) -> tuple[StyledStroke, ...]:
    """Scala e centra i tratti all'interno di uno slot (coordinate locali 0..width_pt, 0..height_pt)."""
    pts_all = [pt for st in strokes for pt in st.points]
    if len(pts_all) < 2 or width_pt <= 0.0 or height_pt <= 0.0:
        return strokes

    xs = [p[0] for p in pts_all]
    ys = [p[1] for p in pts_all]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max_x - min_x
    span_y = max_y - min_y

    target_w = max(1.0, width_pt * pad_ratio)
    target_h = max(1.0, height_pt * pad_ratio)

    needs_scale = span_x > target_w or span_y > target_h
    scale = 1.0
    if needs_scale:
        sx = (target_w / span_x) if span_x > 1e-9 else 1.0
        sy = (target_h / span_y) if span_y > 1e-9 else 1.0
        scale = min(sx, sy)

    out_of_slot = min_x < 0.0 or min_y < 0.0 or max_x > width_pt or max_y > height_pt
    if not needs_scale and not out_of_slot:
        return strokes

    scaled_w = span_x * scale
    scaled_h = span_y * scale
    cx_src = (min_x + max_x) * 0.5
    cy_src = (min_y + max_y) * 0.5
    cx_dst = width_pt * 0.5
    cy_dst = height_pt * 0.5

    fitted: list[StyledStroke] = []
    for st in strokes:
        new_pts = tuple(
            (
                cx_dst + (pt[0] - cx_src) * scale,
                cy_dst + (pt[1] - cy_src) * scale,
            )
            for pt in st.points
        )
        new_w = max(0.25, st.width * scale) if needs_scale else st.width
        fitted.append(replace(st, points=new_pts, width=new_w))
    return tuple(fitted)


def _paginate_fitted_strokes(
    layout: PaginatedLayout,
    strokes_by_item: list[tuple[StyledStroke, ...]],
) -> list[tuple[StyledStroke, ...]]:
    fitted_by_item: list[tuple[StyledStroke, ...]] = list(strokes_by_item)
    for lpage in layout.pages:
        for slot in lpage.slots:
            if 0 <= slot.item_index < len(fitted_by_item):
                fitted_by_item[slot.item_index] = _fit_strokes_to_slot(
                    fitted_by_item[slot.item_index],
                    slot.width_pt,
                    slot.height_pt,
                )
    return fitted_by_item


def build_all_styled_strokes(
    polylines: Sequence[Sequence[Point2D]],
    *,
    config: CompositionConfig | None = None,
    budget_config: BudgetConfig | None = None,
    cache: ParameterCache | None = None,
) -> list[tuple[StyledStroke, ...]]:
    """Calcola gli StyledStroke identici per una lista di polilinee."""
    return [
        build_styled_strokes(poly, config=config, budget_config=budget_config, cache=cache)
        for poly in polylines
    ]


def compose_and_paginate(
    polylines: Sequence[Sequence[Point2D]],
    *,
    page: PageSpec | None = None,
    rows: int = 2,
    cols: int = 2,
    gutter_pt: float = 12.0,
    config: CompositionConfig | None = None,
    budget_config: BudgetConfig | None = None,
    cache: ParameterCache | None = None,
) -> tuple[PaginatedLayout, list[tuple[StyledStroke, ...]]]:
    """Genera i tratti stilizzati per ciascuna polilinea e calcola l'impaginazione."""
    target_page = page if page is not None else make_book_page("book_6x9", margins=MarginsSpec(36, 36, 36, 36))
    strokes_by_item = build_all_styled_strokes(
        polylines,
        config=config,
        budget_config=budget_config,
        cache=cache,
    )
    layout = paginate_items(
        len(polylines),
        page=target_page,
        rows=rows,
        cols=cols,
        gutter_pt=gutter_pt,
    )
    fitted_strokes = _paginate_fitted_strokes(layout, strokes_by_item)
    return layout, fitted_strokes


def export_composition_bundle(
    polylines: Sequence[Sequence[Point2D]],
    output_dir: Path | str,
    *,
    page: PageSpec | None = None,
    rows: int = 2,
    cols: int = 2,
    gutter_pt: float = 12.0,
    dpi: int = 150,
    include_pdf: bool = True,
    config: CompositionConfig | None = None,
    budget_config: BudgetConfig | None = None,
    cache: ParameterCache | None = None,
) -> ExportBundle:
    """Esporta SVG, PNG e opzionalmente PDF usando lo stesso budget della preview."""
    active_budget = budget_config if budget_config is not None else BudgetConfig(mode="full_quality")
    layout, strokes_by_item = compose_and_paginate(
        polylines,
        page=page,
        rows=rows,
        cols=cols,
        gutter_pt=gutter_pt,
        config=config,
        budget_config=active_budget,
        cache=cache,
    )
    out_root = Path(output_dir)
    svg_paths = export_layout_svg(layout, strokes_by_item, out_root / "svg", prefix="kaleido")
    png_paths = export_layout_png(layout, strokes_by_item, out_root / "png", dpi=dpi, prefix="kaleido")
    pdf_path = export_layout_pdf(layout, strokes_by_item, out_root / "kaleido_book.pdf") if include_pdf else None
    return ExportBundle(
        layout=layout,
        svg_files=tuple(svg_paths),
        png_files=tuple(png_paths),
        pdf_file=pdf_path,
    )