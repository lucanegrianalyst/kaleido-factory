"""Calcolo lunghezza percorso, budget dinamico punti e modalita operative."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Sequence

from kaleido_factory.core.validation import Point2D, require_finite_float, require_int, validate_points

RenderMode = Literal["fast_preview", "full_quality"]


@dataclass(frozen=True)
class BudgetConfig:
    """Parametri di controllo del budget punti per modalita operativa."""

    mode: RenderMode = "fast_preview"
    max_points_fast: int = 800
    max_points_full: int = 12000
    min_spacing: float = 0.25
    max_smoothing_passes_fast: int = 2
    max_smoothing_passes_full: int = 12
    max_subdivisions_fast: int = 2
    max_subdivisions_full: int = 6

    def __post_init__(self) -> None:
        if self.mode not in ("fast_preview", "full_quality"):
            raise ValueError(f"Modalita non supportata: {self.mode}")
        f_cap = require_int(self.max_points_fast, "max_points_fast", min_value=8)
        u_cap = require_int(self.max_points_full, "max_points_full", min_value=f_cap)
        spacing = require_finite_float(self.min_spacing, "min_spacing", positive_only=True)
        sf = require_int(self.max_smoothing_passes_fast, "max_smoothing_passes_fast", min_value=0)
        su = require_int(self.max_smoothing_passes_full, "max_smoothing_passes_full", min_value=sf)
        df = require_int(self.max_subdivisions_fast, "max_subdivisions_fast", min_value=0)
        du = require_int(self.max_subdivisions_full, "max_subdivisions_full", min_value=df)
        object.__setattr__(self, "max_points_fast", f_cap)
        object.__setattr__(self, "max_points_full", u_cap)
        object.__setattr__(self, "min_spacing", spacing)
        object.__setattr__(self, "max_smoothing_passes_fast", sf)
        object.__setattr__(self, "max_smoothing_passes_full", su)
        object.__setattr__(self, "max_subdivisions_fast", df)
        object.__setattr__(self, "max_subdivisions_full", du)


@dataclass(frozen=True)
class ComputedBudget:
    """Risultato del budget dinamico applicato al percorso."""

    path_length: float
    point_cap: int
    effective_spacing: float
    allowed_smoothing_passes: int
    allowed_subdivisions: int


def compute_path_length(points: Sequence[Point2D], *, closed: bool = False) -> float:
    """Calcola la lunghezza euclidea totale di una polilinea aperta o chiusa."""
    if not isinstance(closed, bool):
        raise TypeError("closed deve essere booleano.")
    pts = validate_points(points, min_points=0, allow_degenerate=True)
    if len(pts) < 2:
        return 0.0

    total = 0.0
    for i in range(1, len(pts)):
        total += math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])

    if closed:
        total += math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1])
    return total


def compute_point_budget(
    points: Sequence[Point2D],
    *,
    spacing: float,
    smoothing_passes: int = 0,
    subdivisions: int = 0,
    closed: bool = False,
    config: BudgetConfig | None = None,
) -> ComputedBudget:
    """Calcola budget punti, spaziatura effettiva, passate e suddivisioni per la modalita."""
    cfg = BudgetConfig() if config is None else config
    if not isinstance(cfg, BudgetConfig):
        raise TypeError("config deve essere un'istanza di BudgetConfig.")

    sp = require_finite_float(spacing, "spacing", positive_only=True)
    sm = require_int(smoothing_passes, "smoothing_passes", min_value=0)
    sd = require_int(subdivisions, "subdivisions", min_value=0)
    length = compute_path_length(points, closed=closed)

    if cfg.mode == "fast_preview":
        cap = cfg.max_points_fast
        allowed_sm = min(sm, cfg.max_smoothing_passes_fast)
        allowed_sd = min(sd, cfg.max_subdivisions_fast)
    else:
        cap = cfg.max_points_full
        allowed_sm = min(sm, cfg.max_smoothing_passes_full)
        allowed_sd = min(sd, cfg.max_subdivisions_full)

    base_spacing = max(sp, cfg.min_spacing)
    if length <= 0.0:
        effective_spacing = base_spacing
    else:
        needed_points = math.ceil(length / base_spacing) + 1
        if needed_points > cap:
            effective_spacing = length / max(1, cap - 1)
        else:
            effective_spacing = base_spacing

    return ComputedBudget(
        path_length=length,
        point_cap=cap,
        effective_spacing=effective_spacing,
        allowed_smoothing_passes=allowed_sm,
        allowed_subdivisions=allowed_sd,
    )