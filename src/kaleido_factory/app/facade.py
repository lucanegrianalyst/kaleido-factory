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


def _align_strokes_to_slot_origin(
    strokes: tuple[StyledStroke, ...],
    slot_x_pt: float,
    slot_y_pt: float,
    slot_w_pt: float,
    slot_h_pt: float,
) -> tuple[StyledStroke, ...]:
    """Porta i tratti in coordinate locali dello slot (pt) senza alterarli o rimpicciolirli."""
    pts_all = [pt for st in strokes for pt in st.points]
    if not pts_all:
        return strokes

    min_x = min(p[0] for p in pts_all)
    max_x = max(p[0] for p in pts_all)
    min_y = min(p[1] for p in pts_all)
    max_y = max(p[1] for p in pts_all)

    # Se i tratti sono già espressi in coordinate locali dello slot, non traslarli ulteriormente.
    already_local = (
        min_x >= -slot_w_pt * 0.5
        and max_x <= slot_w_pt * 1.5
        and min_y >= -slot_h_pt * 0.5
        and max_y <= slot_h_pt * 1.5
    )
    if already_local:
        return strokes

    aligned: list[StyledStroke] = []
    for st in strokes:
        new_pts = tuple((p[0] - slot_x_pt, p[1] - slot_y_pt) for p in st.points)
        aligned.append(replace(st, points=new_pts))
    return tuple(aligned)


def _paginate_fitted_strokes(
    layout: PaginatedLayout,
    strokes_by_item: list[tuple[StyledStroke, ...]],
) -> list[tuple[StyledStroke, ...]]:
    aligned_by_item: list[tuple[StyledStroke, ...]] = list(strokes_by_item)
    for lpage in layout.pages:
        for slot in lpage.slots:
            if 0 <= slot.item_index < len(aligned_by_item):
                aligned_by_item[slot.item_index] = _align_strokes_to_slot_origin(
                    aligned_by_item[slot.item_index],
                    slot.x_pt,
                    slot.y_pt,
                    slot.width_pt,
                    slot.height_pt,
                )
    return aligned_by_item


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
    single_page_group: bool = False,
) -> tuple[PaginatedLayout, list[tuple[StyledStroke, ...]]]:
    """Genera i tratti stilizzati per ciascuna polilinea e calcola l'impaginazione."""
    target_page = page if page is not None else make_book_page("book_6x9", margins=MarginsSpec(36, 36, 36, 36))
    per_poly_strokes = build_all_styled_strokes(
        polylines,
        config=config,
        budget_config=budget_config,
        cache=cache,
    )
    if single_page_group and len(per_poly_strokes) > 1:
        merged_strokes = tuple(st for group in per_poly_strokes for st in group)
        strokes_by_item = [merged_strokes]
    else:
        strokes_by_item = per_poly_strokes
    layout = paginate_items(
        len(strokes_by_item),
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
    single_page_group: bool = False,
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
        single_page_group=single_page_group,
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