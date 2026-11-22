from __future__ import annotations

from pathlib import Path

from kaleido_factory.app.facade import (
    ExportBundle,
    build_styled_strokes,
    export_composition_bundle,
)


def test_build_styled_strokes_and_bundle_export(tmp_path: Path) -> None:
    polylines = [[(0.0, 0.0), (30.0, 10.0), (15.0, 40.0)]]
    styled = build_styled_strokes(polylines[0])
    assert len(styled) >= 1

    bundle = export_composition_bundle(
        polylines,
        tmp_path / "bundle_out",
        rows=1,
        cols=1,
        dpi=72,
        include_pdf=True,
    )
    assert isinstance(bundle, ExportBundle)
    assert bundle.pdf_file is not None and Path(bundle.pdf_file).exists()
    assert len(bundle.svg_files) == 1 and Path(bundle.svg_files[0]).exists()
    assert len(bundle.png_files) == 1 and Path(bundle.png_files[0]).exists()

def test_compose_and_paginate_preserves_overflow_without_hidden_scaling() -> None:
    from kaleido_factory.app.facade import compose_and_paginate
    from kaleido_factory.layout.formats import make_book_page

    # Tratto più ampio dello slot: non deve venire rimpicciolito di nascosto
    polylines = [[(320.0, 140.0), (600.0, 140.0), (600.0, 420.0), (320.0, 420.0)]]
    page = make_book_page("book_6x9")
    layout, aligned = compose_and_paginate(polylines, page=page, rows=1, cols=1)
    assert layout.total_pages == 1

    pts = [pt for st in aligned[0] for pt in st.points]
    assert pts
    span_x = max(p[0] for p in pts) - min(p[0] for p in pts)
    assert span_x > 200.0
