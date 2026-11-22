"""Test per core/document.py: immutabilita, margini, aspect ratio e polilinee."""

from __future__ import annotations

import math
import pytest

from kaleido_factory.core.document import (
    CoordinateSystemSpec,
    DocumentSpec,
    FrameSpec,
    MarginsSpec,
    PageSpec,
    PolylineItem,
)


def test_page_and_coordinate_aspect_match() -> None:
    page = PageSpec(width_inches=6.0, height_inches=9.0, orientation="landscape", margins=MarginsSpec(36, 36, 36, 36))
    assert page.width_points == pytest.approx(9.0 * 72.0)
    assert page.height_points == pytest.approx(6.0 * 72.0)

    coords = CoordinateSystemSpec(width=1500.0, height=1000.0)
    assert coords.matches_page_aspect(page) is True

    doc = DocumentSpec(
        page=page,
        coordinates=coords,
        polylines=(PolylineItem(points=((0.0, 0.0), (100.0, 100.0)), stroke_width=2.0),),
        enforce_aspect_match=True,
    )
    assert len(doc.polylines) == 1
    with pytest.raises(AttributeError):
        doc.stroke_color = "#FF0000"  # type: ignore[misc]


def test_reject_invalid_polyline_and_frame_values() -> None:
    with pytest.raises(ValueError):
        PolylineItem(points=((0.0, 0.0), (10.0, 10.0)), stroke_width=0.0)
    with pytest.raises(ValueError):
        PolylineItem(points=((0.0, 0.0), (10.0, math.nan)), stroke_width=1.0)
    with pytest.raises(ValueError):
        FrameSpec(width=-1.0, color="#000000")

    page = PageSpec(width_inches=8.0, height_inches=8.0, orientation="square")
    bad_coords = CoordinateSystemSpec(width=800.0, height=400.0)
    with pytest.raises(ValueError):
        DocumentSpec(page=page, coordinates=bad_coords, enforce_aspect_match=True)