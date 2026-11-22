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
