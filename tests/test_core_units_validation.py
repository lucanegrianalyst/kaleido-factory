"""Test unitari per core/units.py e core/validation.py."""

from __future__ import annotations

import math
import pytest

from kaleido_factory.core.units import aspect_ratio, inches_to_points, points_to_inches, resolve_dimensions
from kaleido_factory.core.validation import (
    require_finite_float,
    require_int,
    strip_known_extensions,
    validate_dpi,
    validate_points,
)


def test_points_and_inches_72_rule() -> None:
    assert inches_to_points(2.0) == pytest.approx(144.0)
    assert points_to_inches(144.0) == pytest.approx(2.0)


def test_resolve_dimensions_and_aspect_ratio() -> None:
    assert resolve_dimensions(6.0, 9.0, "portrait") == pytest.approx((6.0, 9.0))
    assert resolve_dimensions(6.0, 9.0, "landscape") == pytest.approx((9.0, 6.0))
    assert resolve_dimensions(6.0, 9.0, "square") == pytest.approx((6.0, 6.0))
    assert aspect_ratio(12.0, 6.0) == pytest.approx(2.0)


def test_reject_bool_and_non_finite() -> None:
    with pytest.raises(TypeError):
        require_int(True, "n")
    with pytest.raises(TypeError):
        require_finite_float(False, "w")
    with pytest.raises(ValueError):
        require_finite_float(math.nan, "w")
    with pytest.raises(ValueError):
        require_finite_float(math.inf, "w")


def test_dpi_and_extension_stripping() -> None:
    assert validate_dpi(300) == 300
    with pytest.raises(TypeError):
        validate_dpi(True)
    with pytest.raises(ValueError):
        validate_dpi(200)
    assert str(strip_known_extensions("exports/tavola.png.pdf")).replace("\\", "/") == "exports/tavola"


def test_points_validation_and_degeneracy() -> None:
    assert validate_points([], min_points=0) == []
    assert validate_points([(-1.5, 2.5), (3.0, -4.0)], min_points=2) == [(-1.5, 2.5), (3.0, -4.0)]
    with pytest.raises(ValueError):
        validate_points([(1.0, 1.0)], min_points=2)
    with pytest.raises(ValueError):
        validate_points([(2.0, 2.0), (2.0, 2.0)], min_points=2, allow_degenerate=False)
