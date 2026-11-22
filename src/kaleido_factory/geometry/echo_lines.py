"""Linee eco a crescere o decrescere con scala e spessore variabili."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from kaleido_factory.core.validation import Point2D, require_finite_float, require_int, validate_points


@dataclass(frozen=True)
class EchoBranch:
    """Singola linea eco trasformata con scala e spessore dedicati."""

    points: tuple[Point2D, ...]
    scale: float
    stroke_width: float


def compute_centroid(points: Sequence[Point2D]) -> Point2D:
    """Calcola il baricentro aritmetico di una sequenza non vuota di punti."""
    pts = validate_points(points, min_points=1, allow_degenerate=True)
    sx = sum(p[0] for p in pts)
    sy = sum(p[1] for p in pts)
    count = float(len(pts))
    return (sx / count, sy / count)


def generate_echo_lines(
    points: Sequence[Point2D],
    *,
    echo_count: int = 3,
    scale_step: float = 0.85,
    base_stroke_width: float = 1.5,
    stroke_step: float = 0.85,
    origin: Point2D | None = None,
    include_original: bool = True,
    max_total_points: int = 12000,
) -> tuple[EchoBranch, ...]:
    """Genera copie eco scalate e con spessore variabile entro max_total_points."""
    count = require_int(echo_count, "echo_count", min_value=0)
    s_step = require_finite_float(scale_step, "scale_step", positive_only=True)
    w_base = require_finite_float(base_stroke_width, "base_stroke_width", positive_only=True)
    w_step = require_finite_float(stroke_step, "stroke_step", positive_only=True)
    cap = require_int(max_total_points, "max_total_points", min_value=2)
    if not isinstance(include_original, bool):
        raise TypeError("include_original deve essere booleano.")

    pts = validate_points(points, min_points=0, allow_degenerate=True)
    if len(pts) < 2:
        return ()

    ox, oy = compute_centroid(pts) if origin is None else validate_points([origin], min_points=1, allow_degenerate=True)[0]
    steps_to_build: list[tuple[float, float]] = []

    if include_original:
        steps_to_build.append((1.0, w_base))

    cur_scale = 1.0
    cur_width = w_base
    for _ in range(count):
        cur_scale *= s_step
        cur_width *= w_step
        steps_to_build.append((cur_scale, max(0.05, cur_width)))

    branches: list[EchoBranch] = []
    used_points = 0
    for sc, wd in steps_to_build:
        if used_points >= cap:
            break
        remaining = cap - used_points
        slice_pts = pts[:remaining]
        transformed = tuple((ox + (p[0] - ox) * sc, oy + (p[1] - oy) * sc) for p in slice_pts)
        branches.append(EchoBranch(points=transformed, scale=sc, stroke_width=wd))
        used_points += len(transformed)

    return tuple(branches)