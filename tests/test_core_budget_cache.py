"""Test per core/point_budget.py e core/cache.py."""

from __future__ import annotations

import pytest

from kaleido_factory.core.cache import ParameterCache, build_cache_key
from kaleido_factory.core.point_budget import BudgetConfig, compute_path_length, compute_point_budget


def test_path_length_open_vs_closed() -> None:
    pts = [(0.0, 0.0), (3.0, 0.0), (3.0, 4.0)]
    assert compute_path_length(pts, closed=False) == pytest.approx(7.0)
    assert compute_path_length(pts, closed=True) == pytest.approx(12.0)
    assert compute_path_length([(1.0, 1.0)], closed=True) == pytest.approx(0.0)


def test_fast_preview_vs_full_quality_budget() -> None:
    long_line = [(float(i), 0.0) for i in range(0, 5001, 10)]
    fast_cfg = BudgetConfig(mode="fast_preview", max_points_fast=100, max_points_full=2000)
    full_cfg = BudgetConfig(mode="full_quality", max_points_fast=100, max_points_full=2000)

    b_fast = compute_point_budget(long_line, spacing=1.0, smoothing_passes=10, subdivisions=5, config=fast_cfg)
    b_full = compute_point_budget(long_line, spacing=1.0, smoothing_passes=10, subdivisions=5, config=full_cfg)

    assert b_fast.point_cap == 100
    assert b_fast.effective_spacing > b_full.effective_spacing
    assert b_fast.allowed_smoothing_passes == fast_cfg.max_smoothing_passes_fast
    assert b_full.allowed_smoothing_passes == 10
    assert b_full.allowed_subdivisions == 5


def test_cache_hit_and_invalidation_on_param_change() -> None:
    cache = ParameterCache(max_entries=16)
    calls = 0

    def work() -> list[int]:
        nonlocal calls
        calls += 1
        return [calls]

    val1, hit1 = cache.get_or_compute("geom", {"mode": "fast_preview", "spacing": 2.0}, work)
    val2, hit2 = cache.get_or_compute("geom", {"mode": "fast_preview", "spacing": 2.0}, work)
    val3, hit3 = cache.get_or_compute("geom", {"mode": "full_quality", "spacing": 2.0}, work)

    assert hit1 is False and hit2 is True and hit3 is False
    assert val1 == val2 == [1]
    assert val3 == [2]
    assert build_cache_key("geom", {"a": 1, "b": 2}) == build_cache_key("geom", {"b": 2, "a": 1})

    removed = cache.invalidate_namespace("geom")
    assert removed == 2
    assert cache.size == 0