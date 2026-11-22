from __future__ import annotations

import pytest

from kaleido_factory.geometry.symmetry import apply_kaleidoscope_symmetry


def test_symmetry_branch_count_without_mirror() -> None:
    pts = [(10.0, 0.0), (20.0, 5.0)]
    branches = apply_kaleidoscope_symmetry(pts, sectors=6, center=(0.0, 0.0), mirror=False)
    assert len(branches) == 6
    assert all(len(b) == 2 for b in branches)


def test_symmetry_branch_count_with_mirror() -> None:
    pts = [(10.0, 2.0), (25.0, 8.0)]
    branches = apply_kaleidoscope_symmetry(pts, sectors=4, center=(0.0, 0.0), mirror=True)
    assert len(branches) == 4
    assert all(len(b) == 2 for b in branches)


def test_symmetry_invalid_sectors_raises() -> None:
    with pytest.raises(ValueError):
        apply_kaleidoscope_symmetry([(1.0, 1.0), (2.0, 2.0)], sectors=0)
