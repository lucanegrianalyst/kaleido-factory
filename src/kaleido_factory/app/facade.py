"""Facciata applicativa per comporre, impaginare ed esportare composizioni kaleidoscopiche."""

from __future__ import annotations

from dataclasses import dataclass
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
    return layout, strokes_by_item


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