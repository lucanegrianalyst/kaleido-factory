"""Test per rendering/svg_exporter.py e rendering/raster_pdf_exporter.py."""

from __future__ import annotations

from pathlib import Path
from PIL import Image

from kaleido_factory.core.document import MarginsSpec
from kaleido_factory.effects.stroke_styles import StyledStroke
from kaleido_factory.layout.formats import make_book_page
from kaleido_factory.layout.pagination import paginate_items
from kaleido_factory.rendering.raster_pdf_exporter import export_layout_pdf, export_layout_png, render_page_png
from kaleido_factory.rendering.svg_exporter import export_layout_svg, render_page_svg


def test_svg_png_and_pdf_export(tmp_path: Path) -> None:
    page = make_book_page("book_6x9", orientation="portrait", margins=MarginsSpec(36, 36, 36, 36))
    layout = paginate_items(2, page=page, rows=2, cols=1, gutter_pt=12.0)

    strokes_item_0 = (StyledStroke(points=((0.0, 0.0), (50.0, 20.0)), width=2.0, opacity=1.0),)
    strokes_item_1 = (StyledStroke(points=((0.0, 0.0), (40.0, 40.0)), width=1.5, opacity=0.8),)
    strokes_by_item = [strokes_item_0, strokes_item_1]

    svg_text = render_page_svg(0, layout, strokes_by_item)
    assert "<svg" in svg_text and "<polyline" in svg_text

    svg_files = export_layout_svg(layout, strokes_by_item, tmp_path / "svg", prefix="sheet")
    assert len(svg_files) == 1 and svg_files[0].is_file()

    img = render_page_png(0, layout, strokes_by_item, dpi=72)
    assert img.size == (int(round(6.0 * 72)), int(round(9.0 * 72)))

    png_files = export_layout_png(layout, strokes_by_item, tmp_path / "png", dpi=72, prefix="sheet")
    assert len(png_files) == 1 and png_files[0].is_file()
    with Image.open(png_files[0]) as opened:
        assert opened.format == "PNG"

    pdf_path = export_layout_pdf(layout, strokes_by_item, tmp_path / "out.pdf")
    assert pdf_path.is_file()
    pdf_bytes = pdf_path.read_bytes()
    assert pdf_bytes.startswith(b"%PDF-1.4") and b"%%EOF" in pdf_bytes