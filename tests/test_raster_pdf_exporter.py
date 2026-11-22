from __future__ import annotations

from pathlib import Path

from kaleido_factory.app.facade import compose_and_paginate
from kaleido_factory.rendering.raster_pdf_exporter import (
    export_layout_pdf,
    export_layout_png,
    render_page_png,
)


def test_render_and_export_png_and_pdf(tmp_path: Path) -> None:
    polylines = [[(5.0, 5.0), (40.0, 15.0), (25.0, 50.0)]]
    layout, paginated_strokes = compose_and_paginate(polylines, rows=1, cols=1)

    img = render_page_png(0, layout, paginated_strokes, dpi=72)
    assert img.size[0] > 0 and img.size[1] > 0

    png_files = export_layout_png(layout, paginated_strokes, tmp_path, dpi=72, prefix="sheet")
    assert len(png_files) == 1 and png_files[0].exists()

    pdf_path = export_layout_pdf(layout, paginated_strokes, tmp_path / "out.pdf")
    assert pdf_path.exists() and pdf_path.stat().st_size > 0
