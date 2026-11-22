"""Ricampionamento uniforme su tutta l'estensione con tetto punti e conservazione estremi/chiusura."""

from __future__ import annotations

import math
from typing import Sequence

from kaleido_factory.core.validation import Point2D, require_finite_float, require_int, validate_points


def _cumulative_lengths(points: Sequence[Point2D], *, closed: bool) -> list[float]:
    acc = [0.0]
    for i in range(1, len(points)):
        seg = math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1])
        acc.append(acc[-1] + seg)
    if closed and len(points) >= 2:
        closing_seg = math.hypot(points[0][0] - points[-1][0], points[0][1] - points[-1][1])
        acc.append(acc[-1] + closing_seg)
    return acc


def _interpolate_at(points: Sequence[Point2D], cum: Sequence[float], target_s: float, *, closed: bool) -> Point2D:
    n = len(points)
    total = cum[-1]
    if total <= 1e-12:
        return points[0]

    s = max(0.0, min(target_s, total))
    seg_count = n if closed else (n - 1)

    for idx in range(seg_count):
        s0 = cum[idx]
        s1 = cum[idx + 1]
        if s <= s1 or idx == seg_count - 1:
            span = s1 - s0
            t = 0.0 if span <= 1e-15 else (s - s0) / span
            a = points[idx]
            b = points[(idx + 1) % n]
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    return points[-1]


def resample_uniform(
    points: Sequence[Point2D],
    *,
    spacing: float,
    max_points: int,
    closed: bool = False,
) -> tuple[Point2D, ...]:
    """Ricampiona uniformemente rispettando max_points, estremi (se aperto) o chiusura (se chiuso)."""
    if not isinstance(closed, bool):
        raise TypeError("closed deve essere booleano.")
    sp = require_finite_float(spacing, "spacing", positive_only=True)
    cap = require_int(max_points, "max_points", min_value=2)
    pts = validate_points(points, min_points=0, allow_degenerate=True)

    if len(pts) < 2:
        return tuple(pts)

    cum = _cumulative_lengths(pts, closed=closed)
    total_len = cum[-1]
    if total_len <= 1e-12:
        return (pts[0],)

    if closed:
        desired_count = max(3, int(math.floor(total_len / sp)))
        count = min(cap, desired_count)
        step = total_len / count
        return tuple(_interpolate_at(pts, cum, i * step, closed=True) for i in range(count))

    desired_count = max(2, int(math.floor(total_len / sp)) + 1)
    count = min(cap, desired_count)
    if count == 2:
        return (pts[0], pts[-1])

    out: list[Point2D] = [pts[0]]
    step = total_len / (count - 1)
    for i in range(1, count - 1):
        out.append(_interpolate_at(pts, cum, i * step, closed=False))
    out.append(pts[-1])
    return tuple(out)