"""Test per geometry/symmetry.py e geometry/echo_lines.py."""

from __future__ import annotations

import math
import pytest

from kaleido_factory.geometry.echo_lines import compute_centroid, generate_echo_lines
from kaleido_factory.geometry.symmetry import apply_kaleidoscope_symmetry


def test_kaleidoscope_sectors_and_mirror() -> None:
    pts = [(10.0, 0.0), (20.0, 5.0)]
    branches = apply_kaleidoscope_symmetry(pts, sectors=4, center=(0.0, 0.0), mirror=True)
    assert len(branches) == 4
    # Settore 0 invariato; settore 1 ruotato di 90 gradi e specchiato.
    assert branches[0][0] == pytest.approx((10.0, 0.0))
    assert branches[1][0][0] == pytest.approx(0.0)
    assert branches[1][0][1] == pytest.approx(10.0)


def test_echo_lines_growing_and_shrinking_with_cap() -> None:
    square = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    cx, cy = compute_centroid(square)
    assert (cx, cy) == pytest.approx((5.0, 5.0))

    shrinking = generate_echo_lines(square, echo_count=3, scale_step=0.8, stroke_step=0.9, origin=(cx, cy))
    assert len(shrinking) == 4
    assert shrinking[-1].scale == pytest.approx(0.8 ** 3)
    assert shrinking[-1].stroke_width < shrinking[0].stroke_width

    growing = generate_echo_lines(square, echo_count=2, scale_step=1.25, stroke_step=1.1, origin=(cx, cy), include_original=False)
    assert len(growing) == 2
    assert growing[0].scale == pytest.approx(1.25)

    capped = generate_echo_lines(square, echo_count=5, scale_step=0.9, max_total_points=10)
    total_pts = sum(len(b.points) for b in capped)
    assert total_pts <= 10


def test_invalid_symmetry_and_echo_inputs() -> None:
    with pytest.raises(ValueError):
        apply_kaleidoscope_symmetry([(0.0, 0.0), (1.0, 1.0)], sectors=0)
    with pytest.raises(ValueError):
        generate_echo_lines([(0.0, 0.0), (1.0, 1.0)], echo_count=1, scale_step=0.0)