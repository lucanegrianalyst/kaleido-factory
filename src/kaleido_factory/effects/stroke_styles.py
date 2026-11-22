"""Trasformazioni di stile e strati visivi deterministici (shading, neon, writing)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from kaleido_factory.core.validation import Point2D, require_finite_float, require_int, validate_points


@dataclass(frozen=True)
class StyledStroke:
    """Singolo strato di tratto pronto per preview ed export."""

    points: tuple[Point2D, ...]
    width: float
    opacity: float
    role: str = "base"


def build_neon_layers(
    points: Sequence[Point2D],
    *,
    core_width: float = 1.5,
    glow_steps: int = 3,
    glow_spread: float = 2.2,
    min_opacity: float = 0.12,
) -> tuple[StyledStroke, ...]:
    """Genera strati di alone (dal piu ampio e tenue al nucleo nitido)."""
    w_core = require_finite_float(core_width, "core_width", positive_only=True)
    steps = require_int(glow_steps, "glow_steps", min_value=1)
    spread = require_finite_float(glow_spread, "glow_spread", positive_only=True)
    op_min = require_finite_float(min_opacity, "min_opacity", positive_only=True)
    if op_min >= 1.0:
        raise ValueError("min_opacity deve essere minore di 1.0.")

    pts = validate_points(points, min_points=0, allow_degenerate=True)
    if len(pts) < 2:
        return ()

    tuple_pts = tuple(pts)
    layers: list[StyledStroke] = []

    for idx in range(steps, 0, -1):
        frac = idx / float(steps)
        width = w_core + (frac * spread * w_core)
        opacity = op_min + ((1.0 - frac) * (0.55 - op_min))
        layers.append(StyledStroke(points=tuple_pts, width=width, opacity=max(0.02, min(1.0, opacity)), role="neon_glow"))

    layers.append(StyledStroke(points=tuple_pts, width=w_core, opacity=1.0, role="neon_core"))
    return tuple(layers)


def build_shading_strokes(
    points: Sequence[Point2D],
    *,
    base_width: float = 1.2,
    hatch_length: float = 6.0,
    hatch_step: int = 2,
    angle_deg: float = 45.0,
) -> tuple[StyledStroke, ...]:
    """Genera tratto principale e brevi segmenti di ombreggiatura deterministica."""
    w = require_finite_float(base_width, "base_width", positive_only=True)
    h_len = require_finite_float(hatch_length, "hatch_length", positive_only=True)
    step = require_int(hatch_step, "hatch_step", min_value=1)
    rad = math.radians(require_finite_float(angle_deg, "angle_deg"))

    pts = validate_points(points, min_points=0, allow_degenerate=True)
    if len(pts) < 2:
        return ()

    strokes: list[StyledStroke] = [StyledStroke(points=tuple(pts), width=w, opacity=1.0, role="base")]
    dx = math.cos(rad) * h_len
    dy = math.sin(rad) * h_len

    for i in range(0, len(pts), step):
        px, py = pts[i]
        seg: tuple[Point2D, Point2D] = ((px, py), (px + dx, py + dy))
        strokes.append(StyledStroke(points=seg, width=max(0.4, w * 0.7), opacity=0.65, role="shading_hatch"))

    return tuple(strokes)


def modulate_writing_stroke(
    points: Sequence[Point2D],
    *,
    base_width: float = 1.6,
    taper: float = 0.35,
    jitter: float = 0.0,
) -> tuple[StyledStroke, ...]:
    """Spezza il tratto in micro-segmenti con rastremazione dolce (stile pennino/scrittura)."""
    w = require_finite_float(base_width, "base_width", positive_only=True)
    tap = require_finite_float(taper, "taper", allow_zero=True)
    jit = require_finite_float(jitter, "jitter", allow_zero=True)
    if tap > 0.9:
        raise ValueError("taper non puo superare 0.9.")

    pts = validate_points(points, min_points=0, allow_degenerate=True)
    if len(pts) < 2:
        return ()

    n_seg = len(pts) - 1
    out: list[StyledStroke] = []
    for i in range(n_seg):
        progress = i / float(max(1, n_seg - 1)) if n_seg > 1 else 0.5
        # Envelope dolce con punte piu sottili agli estremi.
        envelope = 1.0 - tap * abs(2.0 * progress - 1.0)
        seg_w = max(0.25, w * envelope)
        p0 = pts[i]
        p1 = pts[i + 1]
        if jit > 0.0:
            wave = math.sin((i + 1) * 1.7) * jit
            p0 = (p0[0] + wave, p0[1] - wave * 0.5)
        out.append(StyledStroke(points=(p0, p1), width=seg_w, opacity=1.0, role="writing_seg"))

    return tuple(out)