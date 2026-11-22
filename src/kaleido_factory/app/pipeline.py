"""Pipeline di trasformazione geometrica e stilistica condivisa tra preview ed export."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from kaleido_factory.core.cache import ParameterCache
from kaleido_factory.core.point_budget import BudgetConfig, compute_point_budget
from kaleido_factory.core.validation import Point2D, require_finite_float, require_int, validate_points
from kaleido_factory.effects.presets import PresetSpec
from kaleido_factory.effects.stroke_styles import (
    StyledStroke,
    build_neon_layers,
    build_shading_strokes,
    modulate_writing_stroke,
)
from kaleido_factory.geometry.curve_prep import prepare_curve
from kaleido_factory.geometry.echo_lines import compute_centroid, generate_echo_lines
from kaleido_factory.geometry.resampling import resample_uniform
from kaleido_factory.geometry.smoothing import smooth_curve
from kaleido_factory.geometry.subdivision import subdivide_curve
from kaleido_factory.geometry.symmetry import apply_kaleidoscope_symmetry


@dataclass(frozen=True)
class CompositionConfig:
    """Parametri di composizione per una singola polilinea."""

    closed: bool = False
    spacing: float = 4.0
    smoothing_passes: int = 1
    smoothing_weight: float = 0.5
    subdivisions: int = 1
    corner_ratio: float = 0.25
    sectors: int = 6
    mirror: bool = True
    center: Point2D = (0.0, 0.0)
    echo_count: int = 0
    scale_step: float = 0.85
    base_stroke_width: float = 1.5
    stroke_step: float = 0.85
    effects: tuple[str, ...] = ()

    @classmethod
    def from_preset(cls, preset: PresetSpec, *, closed: bool = False, center: Point2D = (0.0, 0.0)) -> "CompositionConfig":
        if not isinstance(preset, PresetSpec):
            raise TypeError("preset deve essere un'istanza di PresetSpec.")
        return cls(
            closed=closed,
            smoothing_passes=preset.smoothing_passes,
            subdivisions=preset.subdivisions,
            sectors=preset.sectors,
            mirror=preset.mirror,
            center=center,
            echo_count=preset.echo_count,
            scale_step=preset.scale_step,
            stroke_step=preset.stroke_step,
            effects=preset.effects,
        )


def _apply_effects_to_branch(pts: tuple[Point2D, ...], width: float, effects: tuple[str, ...]) -> list[StyledStroke]:
    if len(pts) < 2:
        return []
    effect_set = {e.strip().lower() for e in effects if e.strip()}
    if "neon" in effect_set:
        return list(build_neon_layers(pts, core_width=width))
    if "shading" in effect_set:
        return list(build_shading_strokes(pts, base_width=width))
    if "writing" in effect_set:
        return list(modulate_writing_stroke(pts, base_width=width))
    return [StyledStroke(points=pts, width=width, opacity=1.0, role="base")]


def build_styled_strokes(
    points: Sequence[Point2D],
    *,
    config: CompositionConfig | None = None,
    budget_config: BudgetConfig | None = None,
    cache: ParameterCache | None = None,
) -> tuple[StyledStroke, ...]:
    """Esegue la pipeline completa e restituisce gli StyledStroke pronti per preview o export."""
    cfg = CompositionConfig() if config is None else config
    if not isinstance(cfg, CompositionConfig):
        raise TypeError("config deve essere un'istanza di CompositionConfig.")
    b_cfg = BudgetConfig() if budget_config is None else budget_config
    if not isinstance(b_cfg, BudgetConfig):
        raise TypeError("budget_config deve essere un'istanza di BudgetConfig.")

    pts = validate_points(points, min_points=0, allow_degenerate=True)
    sp = require_finite_float(cfg.spacing, "spacing", positive_only=True)
    sm_w = require_finite_float(cfg.smoothing_weight, "smoothing_weight", allow_zero=True)
    c_ratio = require_finite_float(cfg.corner_ratio, "corner_ratio", allow_zero=True)
    sec = require_int(cfg.sectors, "sectors", min_value=1)
    sm_p = require_int(cfg.smoothing_passes, "smoothing_passes", min_value=0)
    sub_i = require_int(cfg.subdivisions, "subdivisions", min_value=0)

    def _compute() -> tuple[StyledStroke, ...]:
        prepared = prepare_curve(pts, closed=cfg.closed)
        if not prepared.is_drawable:
            return ()

        budget = compute_point_budget(
            prepared.points,
            spacing=sp,
            smoothing_passes=sm_p,
            subdivisions=sub_i,
            closed=prepared.closed,
            config=b_cfg,
        )
        cur = resample_uniform(
            prepared.points,
            spacing=budget.effective_spacing,
            max_points=budget.point_cap,
            closed=prepared.closed,
        )
        cur = smooth_curve(cur, passes=budget.allowed_smoothing_passes, weight=sm_w, closed=prepared.closed)
        cur = subdivide_curve(
            cur,
            iterations=budget.allowed_subdivisions,
            corner_ratio=c_ratio,
            closed=prepared.closed,
            max_points=budget.point_cap,
        )

        branches = apply_kaleidoscope_symmetry(cur, sectors=sec, center=cfg.center, mirror=cfg.mirror)
        styled_out: list[StyledStroke] = []

        for branch in branches:
            if len(branch) < 2:
                continue
            if cfg.echo_count > 0:
                origin = compute_centroid(branch)
                echoes = generate_echo_lines(
                    branch,
                    echo_count=cfg.echo_count,
                    scale_step=cfg.scale_step,
                    base_stroke_width=cfg.base_stroke_width,
                    stroke_step=cfg.stroke_step,
                    origin=origin,
                    include_original=True,
                    max_total_points=budget.point_cap * max(1, cfg.echo_count + 1),
                )
                for echo in echoes:
                    styled_out.extend(_apply_effects_to_branch(echo.points, echo.stroke_width, cfg.effects))
            else:
                styled_out.extend(_apply_effects_to_branch(branch, cfg.base_stroke_width, cfg.effects))

        return tuple(styled_out)

    if cache is None:
        return _compute()

    params = {
        "points": pts,
        "closed": cfg.closed,
        "spacing": sp,
        "smoothing_passes": sm_p,
        "smoothing_weight": sm_w,
        "subdivisions": sub_i,
        "corner_ratio": c_ratio,
        "sectors": sec,
        "mirror": cfg.mirror,
        "center": cfg.center,
        "echo_count": cfg.echo_count,
        "scale_step": cfg.scale_step,
        "base_stroke_width": cfg.base_stroke_width,
        "stroke_step": cfg.stroke_step,
        "effects": cfg.effects,
        "mode": b_cfg.mode,
        "max_points_fast": b_cfg.max_points_fast,
        "max_points_full": b_cfg.max_points_full,
    }
    result, _ = cache.get_or_compute("pipeline.strokes", params, _compute)
    return result