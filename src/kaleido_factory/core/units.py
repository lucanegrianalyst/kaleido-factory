"""Conversioni unita fisiche (72 pt/in), orientamenti e rapporti d'aspetto."""

from __future__ import annotations

import math
from typing import Literal

POINTS_PER_INCH: float = 72.0
Orientation = Literal["portrait", "landscape", "square"]


def _check_positive_finite(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label} deve essere numerico (non booleano).")
    num = float(value)
    if not math.isfinite(num) or num <= 0.0:
        raise ValueError(f"{label} deve essere finito e maggiore di zero.")
    return num


def inches_to_points(inches: float) -> float:
    """Converte pollici in punti tipografici (72 pt/in)."""
    return _check_positive_finite(inches, "inches") * POINTS_PER_INCH


def points_to_inches(points: float) -> float:
    """Converte punti tipografici (72 pt/in) in pollici."""
    return _check_positive_finite(points, "points") / POINTS_PER_INCH


def resolve_dimensions(width_inches: float, height_inches: float, orientation: Orientation) -> tuple[float, float]:
    """Applica l'orientamento (portrait, landscape, square) a dimensioni in pollici."""
    w = _check_positive_finite(width_inches, "width_inches")
    h = _check_positive_finite(height_inches, "height_inches")
    if orientation == "square":
        side = min(w, h)
        return (side, side)
    if orientation == "landscape":
        return (max(w, h), min(w, h))
    if orientation == "portrait":
        return (min(w, h), max(w, h))
    raise ValueError(f"Orientamento non supportato: {orientation}")


def aspect_ratio(width: float, height: float) -> float:
    """Calcola il rapporto larghezza/altezza per valori positivi e finiti."""
    w = _check_positive_finite(width, "width")
    h = _check_positive_finite(height, "height")
    return w / h
