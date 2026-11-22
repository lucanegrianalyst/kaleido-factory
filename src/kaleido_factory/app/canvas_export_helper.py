"""Helper per esportazione e diagnostica posizioni del canvas interattivo."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Sequence

from kaleido_factory.app.canvas_page_space import CanvasPageSpace
from kaleido_factory.app.facade import export_composition_bundle
from kaleido_factory.app.pipeline import CompositionConfig
from kaleido_factory.core.cache import ParameterCache
from kaleido_factory.core.document import PageSpec
from kaleido_factory.core.point_budget import BudgetConfig
from kaleido_factory.core.validation import Point2D


def format_debug_pos(
    space: CanvasPageSpace,
    cfg: CompositionConfig,
    canvas_w: float,
    canvas_h: float,
) -> str:
    """Restituisce una stringa sintetica con coordinate di canvas, slot e centro."""
    slot_pt = space.slots_pt[0] if space.slots_pt else None
    slot_px = space.slot_rects_px[0] if space.slot_rects_px else None
    sc_pt = space.canvas_points_to_slot_local_pt([cfg.center], slot_index=0)[0]
    s_px_str = (
        f"({slot_px.x0:.1f},{slot_px.y0:.1f}..{slot_px.x1:.1f},{slot_px.y1:.1f})"
        if slot_px
        else "none"
    )
    s_pt_str = (
        f"({slot_pt.x_pt:.1f},{slot_pt.y_pt:.1f} {slot_pt.width_pt:.1f}x{slot_pt.height_pt:.1f})"
        if slot_pt
        else "none"
    )
    return (
        f"canvas={canvas_w:.0f}x{canvas_h:.0f} scale={space.scale_pt_to_px:.3f} "
        f"cfg.center=({cfg.center[0]:.1f},{cfg.center[1]:.1f}) "
        f"slot_center_pt=({sc_pt[0]:.1f},{sc_pt[1]:.1f}) slot_px={s_px_str} slot_pt={s_pt_str}"
    )


def export_canvas_bundle(
    polylines: Sequence[Sequence[Point2D]],
    *,
    space: CanvasPageSpace,
    cfg: CompositionConfig,
    page: PageSpec,
    rows: int,
    cols: int,
    gutter_pt: float,
    budget_cfg: BudgetConfig,
    cache: ParameterCache,
    fmt: str,
    out_dir: Path,
) -> None:
    """Converte i tratti dal canvas allo slot e avvia l'esportazione."""
    if not polylines:
        raise ValueError("Nessun tratto da esportare.")
    slot_polys = [
        space.canvas_points_to_slot_local_pt(poly, slot_index=0)
        for poly in polylines
    ]
    slot_center = space.canvas_points_to_slot_local_pt([cfg.center], slot_index=0)[0]
    export_cfg = replace(cfg, center=slot_center)
    export_composition_bundle(
        slot_polys,
        out_dir,
        page=page,
        rows=rows,
        cols=cols,
        gutter_pt=gutter_pt,
        dpi=150,
        include_pdf=(fmt == "pdf"),
        config=export_cfg,
        budget_config=budget_cfg,
        cache=cache,
        single_page_group=(rows == 1 and cols == 1),
    )
