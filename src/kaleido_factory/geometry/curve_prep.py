"""Preparazione curve aperte e loop chiusi, inclusi loop a 2 punti e segmenti degeneri."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from kaleido_factory.core.validation import Point2D, require_finite_float, validate_points


@dataclass(frozen=True)
class PreparedCurve:
    """Percorso normalizzato pronto per smoothing, suddivisione o ricampionamento."""

    points: tuple[Point2D, ...]
    closed: bool
    is_drawable: bool


def collapse_near_duplicate_points(
    points: Sequence[Point2D],
    *,
    eps: float = 1e-9,
) -> list[Point2D]:
    """Rimuove punti consecutivi coincidenti o separati da distanza quasi nulla."""
    tol = require_finite_float(eps, "eps", allow_zero=True)
    cleaned = validate_points(points, min_points=0, allow_degenerate=True)
    if not cleaned:
        return []

    result: list[Point2D] = [cleaned[0]]
    for pt in cleaned[1:]:
        prev = result[-1]
        if math.hypot(pt[0] - prev[0], pt[1] - prev[1]) > tol:
            result.append(pt)
    return result


def build_two_point_closed_base(p0: Point2D, p1: Point2D) -> tuple[Point2D, ...]:
    """Costruisce una base chiusa iniziale a 4 vertici per un loop chiuso con 2 punti distinti."""
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    length = math.hypot(dx, dy)
    if length <= 1e-12:
        return (p0,)

    # Perpendicolare normalizzata con spessore minimo proporzionale per formare un loop non degenere.
    nx = -dy / length
    ny = dx / length
    offset = max(length * 0.15, 1e-6)
    mid_x = 0.5 * (p0[0] + p1[0])
    mid_y = 0.5 * (p0[1] + p1[1])

    q_up: Point2D = (mid_x + nx * offset, mid_y + ny * offset)
    q_dn: Point2D = (mid_x - nx * offset, mid_y - ny * offset)
    return (p0, q_up, p1, q_dn)


def prepare_curve(
    points: Sequence[Point2D],
    *,
    closed: bool = False,
    eps: float = 1e-9,
) -> PreparedCurve:
    """Prepara una curva aperta o un loop chiuso gestendo 0/1/2 punti e segmenti nulli."""
    if not isinstance(closed, bool):
        raise TypeError("closed deve essere booleano.")

    deduped = collapse_near_duplicate_points(points, eps=eps)
    if len(deduped) < 2:
        return PreparedCurve(points=tuple(deduped), closed=closed, is_drawable=False)

    if not closed:
        return PreparedCurve(points=tuple(deduped), closed=False, is_drawable=True)

    # Loop chiuso: se dopo la pulizia restano 2 punti distinti, crea base chiusa iniziale.
    if len(deduped) == 2:
        base = build_two_point_closed_base(deduped[0], deduped[1])
        return PreparedCurve(points=base, closed=True, is_drawable=len(base) >= 3)

    # Rimuove eventuale punto finale coincidente con l'inizio su loop chiuso.
    if math.hypot(deduped[-1][0] - deduped[0][0], deduped[-1][1] - deduped[0][1]) <= require_finite_float(
        eps, "eps", allow_zero=True
    ):
        deduped = deduped[:-1]

    if len(deduped) < 3:
        if len(deduped) == 2:
            base = build_two_point_closed_base(deduped[0], deduped[1])
            return PreparedCurve(points=base, closed=True, is_drawable=len(base) >= 3)
        return PreparedCurve(points=tuple(deduped), closed=True, is_drawable=False)

    return PreparedCurve(points=tuple(deduped), closed=True, is_drawable=True)