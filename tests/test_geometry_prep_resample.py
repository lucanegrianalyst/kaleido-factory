"""Test per geometry/curve_prep.py e geometry/resampling.py."""

from __future__ import annotations

import math
import pytest

from kaleido_factory.geometry.curve_prep import collapse_near_duplicate_points, prepare_curve
from kaleido_factory.geometry.resampling import resample_uniform


def test_empty_single_and_degenerate_points() -> None:
    assert prepare_curve([], closed=False).is_drawable is False
    assert prepare_curve([(5.0, 5.0)], closed=True).is_drawable is False
    assert collapse_near_duplicate_points([(1.0, 1.0), (1.0 + 1e-12, 1.0), (4.0, 1.0)]) == [(1.0, 1.0), (4.0, 1.0)]


def test_two_point_closed_loop_builds_base() -> None:
    prepared = prepare_curve([(0.0, 0.0), (10.0, 0.0)], closed=True)
    assert prepared.closed is True
    assert prepared.is_drawable is True
    assert len(prepared.points) >= 4
    assert prepared.points[0] == (0.0, 0.0)


def test_resample_open_keeps_endpoints_and_respects_cap() -> None:
    line = [(0.0, 0.0), (100.0, 0.0)]
    sampled = resample_uniform(line, spacing=5.0, max_points=10, closed=False)
    assert len(sampled) == 10
    assert sampled[0] == (0.0, 0.0)
    assert sampled[-1] == (100.0, 0.0)


def test_resample_closed_uniform_spacing() -> None:
    square = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    sampled = resample_uniform(square, spacing=5.0, max_points=50, closed=True)
    assert len(sampled) == 8
    dists = [
        math.hypot(sampled[(i + 1) % len(sampled)][0] - sampled[i][0], sampled[(i + 1) % len(sampled)][1] - sampled[i][1])
        for i in range(len(sampled))
    ]
    for d in dists:
        assert d == pytest.approx(5.0)