"""Filtri di smoothing per percorsi aperti e chiusi con controllo di passate e peso."""

from __future__ import annotations

from typing import Sequence

from kaleido_factory.core.validation import Point2D, require_finite_float, require_int, validate_points


def _smooth_once(points: list[Point2D], *, weight: float, closed: bool) -> list[Point2D]:
    n = len(points)
    if n < 3:
        return list(points)

    out: list[Point2D] = []
    if closed:
        for i in range(n):
            prev_pt = points[(i - 1) % n]
            curr_pt = points[i]
            next_pt = points[(i + 1) % n]
            avg_x = 0.5 * (prev_pt[0] + next_pt[0])
            avg_y = 0.5 * (prev_pt[1] + next_pt[1])
            nx = curr_pt[0] + weight * (avg_x - curr_pt[0])
            ny = curr_pt[1] + weight * (avg_y - curr_pt[1])
            out.append((nx, ny))
        return out

    # Percorso aperto: conserva primo e ultimo punto.
    out.append(points[0])
    for i in range(1, n - 1):
        prev_pt = points[i - 1]
        curr_pt = points[i]
        next_pt = points[i + 1]
        avg_x = 0.5 * (prev_pt[0] + next_pt[0])
        avg_y = 0.5 * (prev_pt[1] + next_pt[1])
        nx = curr_pt[0] + weight * (avg_x - curr_pt[0])
        ny = curr_pt[1] + weight * (avg_y - curr_pt[1])
        out.append((nx, ny))
    out.append(points[-1])
    return out


def smooth_curve(
    points: Sequence[Point2D],
    *,
    passes: int = 1,
    weight: float = 0.5,
    closed: bool = False,
) -> tuple[Point2D, ...]:
    """Applica N passate di smoothing a un percorso aperto o chiuso con peso in [0.0, 1.0]."""
    if not isinstance(closed, bool):
        raise TypeError("closed deve essere booleano.")
    n_passes = require_int(passes, "passes", min_value=0)
    w = require_finite_float(weight, "weight", allow_zero=True)
    if w > 1.0:
        raise ValueError("weight deve essere compreso tra 0.0 e 1.0.")

    pts = validate_points(points, min_points=0, allow_degenerate=True)
    if len(pts) < 2 or n_passes == 0 or w == 0.0:
        return tuple(pts)

    current = list(pts)
    for _ in range(n_passes):
        current = _smooth_once(current, weight=w, closed=closed)
    return tuple(current)