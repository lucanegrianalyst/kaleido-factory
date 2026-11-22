from __future__ import annotations

from pathlib import Path

from kaleido_factory.app.facade import build_styled_strokes, compose_and_paginate
from kaleido_factory.rendering.svg_exporter import export_layout_svg, render_page_svg


def test_render_and_export_svg(tmp_path: Path) -> None:
    polylines = [[(10.0, 10.0), (50.0, 20.0), (30.0, 60.0)]]
    layout, paginated_strokes = compose_and_paginate(polylines, rows=1, cols=1)
    _ = build_styled_strokes(polylines[0])

    svg_text = render_page_svg(0, layout, paginated_strokes)
    assert "<svg" in svg_text and "</svg>" in svg_text

    written = export_layout_svg(layout, paginated_strokes, tmp_path, prefix="test_page")
    assert len(written) == 1
    assert written[0].exists() and written[0].stat().st_size > 0
