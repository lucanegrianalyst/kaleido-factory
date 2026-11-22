"""Trasformazioni di simmetria radiale e speculare (kaleidoscopio)."""

from __future__ import annotations

import math
from typing import Sequence

from kaleido_factory.core.validation import Point2D, require_finite_float, require_int, validate_points


def _rotate_around(pt: Point2D, cx: float, cy: float, angle_rad: float) -> Point2D:
    dx = pt[0] - cx
    dy = pt[1] - cy
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    rx = dx * cos_a - dy * sin_a
    ry = dx * sin_a + dy * cos_a
    return (cx + rx, cy + ry)


def _reflect_across_axis(pt: Point2D, cx: float, cy: float, axis_angle_rad: float) -> Point2D:
    """Riflette un punto rispetto a una retta passante per (cx, cy) con angolo axis_angle_rad."""
    dx = pt[0] - cx
    dy = pt[1] - cy
    two_theta = 2.0 * axis_angle_rad
    cos_2 = math.cos(two_theta)
    sin_2 = math.sin(two_theta)
    rx = dx * cos_2 + dy * sin_2
    ry = dx * sin_2 - dy * cos_2
    return (cx + rx, cy + ry)


def apply_kaleidoscope_symmetry(
    points: Sequence[Point2D],
    *,
    sectors: int = 6,
    center: Point2D = (0.0, 0.0),
    mirror: bool = True,
    base_angle_deg: float = 0.0,
) -> tuple[tuple[Point2D, ...], ...]:
    """Genera i rami/settori di simmetria kaleidoscopica attorno a center."""
    n_sectors = require_int(sectors, "sectors", min_value=1)
    if not isinstance(mirror, bool):
        raise TypeError("mirror deve essere booleano.")
    angle_offset = math.radians(require_finite_float(base_angle_deg, "base_angle_deg"))
    cx, cy = validate_points([center], min_points=1, allow_degenerate=True)[0]
    pts = validate_points(points, min_points=0, allow_degenerate=True)
    if not pts:
        return ()

    sector_step = (2.0 * math.pi) / n_sectors
    branches: list[tuple[Point2D, ...]] = []

    for idx in range(n_sectors):
        theta = angle_offset + idx * sector_step
        if mirror and (idx % 2 == 1):
            # Riflette rispetto all'asse del settore corrente così i bordi combaciano.
            axis_angle = angle_offset + (idx - 0.5) * sector_step
            branch = tuple(_reflect_across_axis(p, cx, cy, axis_angle) for p in pts)
        else:
            branch = tuple(_rotate_around(p, cx, cy, theta) for p in pts)
        branches.append(branch)

    return tuple(branches)