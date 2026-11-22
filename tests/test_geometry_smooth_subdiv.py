"""Test per geometry/smoothing.py e geometry/subdivision.py."""

from __future__ import annotations

import pytest

from kaleido_factory.geometry.smoothing import smooth_curve
from kaleido_factory.geometry.subdivision import subdivide_curve


def test_smooth_open_keeps_endpoints_and_reduces_spike() -> None:
    spike = [(0.0, 0.0), (5.0, 10.0), (10.0, 0.0)]
    smoothed = smooth_curve(spike, passes=2, weight=0.5, closed=False)
    assert smoothed[0] == (0.0, 0.0)
    assert smoothed[-1] == (10.0, 0.0)
    assert smoothed[1][1] < 10.0


def test_smooth_closed_wraps_around() -> None:
    loop = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    smoothed = smooth_curve(loop, passes=1, weight=0.5, closed=True)
    assert len(smoothed) == 4
    assert all(isinstance(pt[0], float) and isinstance(pt[1], float) for pt in smoothed)


def test_subdivide_open_and_respects_max_points() -> None:
    poly = [(0.0, 0.0), (10.0, 10.0), (20.0, 0.0)]
    sub = subdivide_curve(poly, iterations=2, corner_ratio=0.25, closed=False, max_points=500)
    assert sub[0] == (0.0, 0.0)
    assert sub[-1] == (20.0, 0.0)
    assert len(sub) > len(poly)

    capped = subdivide_curve(poly, iterations=8, corner_ratio=0.25, closed=True, max_points=24)
    assert len(capped) <= 24


def test_invalid_smoothing_and_subdivision_params() -> None:
    with pytest.raises(ValueError):
        smooth_curve([(0.0, 0.0), (1.0, 1.0)], passes=1, weight=1.5)
    with pytest.raises(ValueError):
        subdivide_curve([(0.0, 0.0), (1.0, 1.0)], iterations=1, corner_ratio=0.8)