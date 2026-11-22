"""Demo CLI di composizione, impaginazione ed export SVG/PNG/PDF per kaleido_factory."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from kaleido_factory.app.facade import export_composition_bundle
from kaleido_factory.app.pipeline import CompositionConfig
from kaleido_factory.core.document import MarginsSpec
from kaleido_factory.layout.formats import make_book_page


def main() -> None:
    polylines = [
        [(12.0, 4.0), (28.0, 14.0), (22.0, 32.0), (8.0, 24.0)],
        [(10.0, 8.0), (30.0, 10.0), (18.0, 34.0)],
        [(6.0, 12.0), (26.0, 6.0), (34.0, 28.0), (14.0, 30.0)],
        [(14.0, 2.0), (24.0, 20.0), (10.0, 35.0)],
    ]

    cfg = CompositionConfig(
        closed=False,
        spacing=3.5,
        smoothing_passes=2,
        subdivisions=2,
        sectors=8,
        mirror=True,
        center=(45.0, 45.0),
        echo_count=2,
        scale_step=0.84,
        base_stroke_width=1.4,
        stroke_step=0.88,
        effects=("shading",),
    )

    page = make_book_page("book_6x9", orientation="portrait", margins=MarginsSpec(36, 36, 36, 36))
    out_dir = Path(r"C:\kaleido_factory\output\demo_01")

    bundle = export_composition_bundle(
        polylines,
        out_dir,
        page=page,
        rows=2,
        cols=2,
        gutter_pt=14.0,
        dpi=150,
        include_pdf=True,
        config=cfg,
    )

    print("Pagine:", bundle.layout.total_pages)
    print("SVG:", [str(p) for p in bundle.svg_files])
    print("PNG:", [str(p) for p in bundle.png_files])
    print("PDF:", str(bundle.pdf_file))


if __name__ == "__main__":
    main()