"""Suddivisione e interpolazione fluida di curve aperte e loop chiusi con tetto di sicurezza."""

from __future__ import annotations

from typing import Sequence

from kaleido_factory.core.validation import Point2D, require_finite_float, require_int, validate_points


def _chaikin_step(points: list[Point2D], *, ratio: float, closed: bool) -> list[Point2D]:
    n = len(points)
    if n < 2:
        return list(points)

    out: list[Point2D] = []
    if not closed:
        out.append(points[0])
        for i in range(n - 1):
            p0 = points[i]
            p1 = points[i + 1]
            q = (p0[0] + ratio * (p1[0] - p0[0]), p0[1] + ratio * (p1[1] - p0[1]))
            r = (p1[0] + ratio * (p0[0] - p1[0]), p1[1] + ratio * (p0[1] - p1[1]))
            out.append(q)
            out.append(r)
        out.append(points[-1])
        return out

    # Loop chiuso: elabora tutti i segmenti inclusa la chiusura.
    for i in range(n):
        p0 = points[i]
        p1 = points[(i + 1) % n]
        q = (p0[0] + ratio * (p1[0] - p0[0]), p0[1] + ratio * (p1[1] - p0[1]))
        r = (p1[0] + ratio * (p0[0] - p1[0]), p1[1] + ratio * (p0[1] - p1[1]))
        out.append(q)
        out.append(r)
    return out


def subdivide_curve(
    points: Sequence[Point2D],
    *,
    iterations: int = 1,
    corner_ratio: float = 0.25,
    closed: bool = False,
    max_points: int = 12000,
) -> tuple[Point2D, ...]:
    """Suddivide e arrotonda progressivamente la curva rispettando max_points."""
    if not isinstance(closed, bool):
        raise TypeError("closed deve essere booleano.")
    iters = require_int(iterations, "iterations", min_value=0)
    ratio = require_finite_float(corner_ratio, "corner_ratio", positive_only=False, allow_zero=True)
    if ratio > 0.5:
        raise ValueError("corner_ratio deve essere compreso tra 0.0 e 0.5.")
    cap = require_int(max_points, "max_points", min_value=2)

    pts = validate_points(points, min_points=0, allow_degenerate=True)
    if len(pts) < 2 or iters == 0:
        return tuple(pts[:cap])

    current = list(pts)
    for _ in range(iters):
        nxt = _chaikin_step(current, ratio=ratio, closed=closed)
        if len(nxt) > cap:
            break
        current = nxt

    return tuple(current[:cap])