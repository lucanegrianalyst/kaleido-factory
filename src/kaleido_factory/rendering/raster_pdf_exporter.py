"""Esportatori PNG (tramite Pillow e DPI) e PDF multipagina (in punti 72 pt/in)."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw

from kaleido_factory.core.units import POINTS_PER_INCH
from kaleido_factory.core.validation import require_dpi, require_finite_float, validate_points
from kaleido_factory.effects.stroke_styles import StyledStroke
from kaleido_factory.layout.pagination import PaginatedLayout


def _pt_to_px(value_pt: float, dpi: int) -> float:
    return value_pt * (dpi / POINTS_PER_INCH)


def render_page_png(
    page_index: int,
    layout: PaginatedLayout,
    strokes_by_item: Sequence[Sequence[StyledStroke]],
    *,
    dpi: int = 150,
    stroke_rgb: tuple[int, int, int] = (17, 17, 17),
) -> Image.Image:
    """Renderizza una pagina del layout in un oggetto PIL Image RGB."""
    if not isinstance(layout, PaginatedLayout):
        raise TypeError("layout deve essere un'istanza di PaginatedLayout.")
    if page_index < 0 or page_index >= layout.total_pages:
        raise IndexError("page_index fuori intervallo.")
    valid_dpi = require_dpi(dpi)

    lpage = layout.pages[page_index]
    px_w = max(1, int(round(_pt_to_px(lpage.page.width_points, valid_dpi))))
    px_h = max(1, int(round(_pt_to_px(lpage.page.height_points, valid_dpi))))

    img = Image.new("RGB", (px_w, px_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    for slot in lpage.slots:
        if slot.item_index < 0 or slot.item_index >= len(strokes_by_item):
            continue
        item_strokes = strokes_by_item[slot.item_index]
        ox = _pt_to_px(slot.x_pt, valid_dpi)
        oy = _pt_to_px(slot.y_pt, valid_dpi)

        for st in item_strokes:
            if not isinstance(st, StyledStroke):
                continue
            pts = validate_points(st.points, min_points=0, allow_degenerate=True)
            if len(pts) < 2:
                continue
            w_pt = require_finite_float(st.width, "stroke.width", positive_only=True)
            w_px = max(1, int(round(_pt_to_px(w_pt, valid_dpi))))
            mapped = [(ox + _pt_to_px(p[0], valid_dpi), oy + _pt_to_px(p[1], valid_dpi)) for p in pts]
            draw.line(mapped, fill=stroke_rgb, width=w_px)

    return img


def export_layout_png(
    layout: PaginatedLayout,
    strokes_by_item: Sequence[Sequence[StyledStroke]],
    output_dir: Path | str,
    *,
    dpi: int = 150,
    prefix: str = "page",
) -> list[Path]:
    """Esporta ogni pagina del layout come file PNG con metadati DPI."""
    if not isinstance(layout, PaginatedLayout):
        raise TypeError("layout deve essere un'istanza di PaginatedLayout.")
    if not isinstance(prefix, str) or not prefix.strip():
        raise ValueError("prefix deve essere una stringa non vuota.")
    valid_dpi = require_dpi(dpi)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for idx in range(layout.total_pages):
        img = render_page_png(idx, layout, strokes_by_item, dpi=valid_dpi)
        target = out_path / f"{prefix.strip()}_{idx + 1:03d}.png"
        img.save(target, format="PNG", dpi=(valid_dpi, valid_dpi))
        written.append(target)

    return written


def export_layout_pdf(
    layout: PaginatedLayout,
    strokes_by_item: Sequence[Sequence[StyledStroke]],
    output_pdf: Path | str,
) -> Path:
    """Esporta il layout multipagina in un file PDF valido con dimensioni in punti (72 pt/in)."""
    if not isinstance(layout, PaginatedLayout):
        raise TypeError("layout deve essere un'istanza di PaginatedLayout.")
    if layout.total_pages == 0:
        raise ValueError("Impossibile esportare un layout senza pagine.")

    target = Path(output_pdf)
    target.parent.mkdir(parents=True, exist_ok=True)

    # Costruisce un documento PDF 1.4 minimale e valido con una pagina per LayoutPage.
    objects: list[bytes] = []

    def add_obj(body: str) -> int:
        objects.append(body.encode("latin-1"))
        return len(objects)

    catalog_id = add_obj("<< /Type /Catalog /Pages 2 0 R >>")
    pages_placeholder_idx = len(objects)
    add_obj("")  # Segnaposto per /Pages

    page_ids: list[int] = []
    for lpage in layout.pages:
        w_pt = lpage.page.width_points
        h_pt = lpage.page.height_points
        stream_ops: list[str] = []

        for slot in lpage.slots:
            if slot.item_index < 0 or slot.item_index >= len(strokes_by_item):
                continue
            item_strokes = strokes_by_item[slot.item_index]
            for st in item_strokes:
                if not isinstance(st, StyledStroke):
                    continue
                pts = validate_points(st.points, min_points=0, allow_degenerate=True)
                if len(pts) < 2:
                    continue
                w_stroke = require_finite_float(st.width, "stroke.width", positive_only=True)
                stream_ops.append(f"{w_stroke:.3f} w")
                # Conversione top-down (layout) -> bottom-up (PDF)
                x0 = slot.x_pt + pts[0][0]
                y0 = h_pt - (slot.y_pt + pts[0][1])
                stream_ops.append(f"{x0:.3f} {y0:.3f} m")
                for p in pts[1:]:
                    px = slot.x_pt + p[0]
                    py = h_pt - (slot.y_pt + p[1])
                    stream_ops.append(f"{px:.3f} {py:.3f} l")
                stream_ops.append("S")

        content_data = ("\n".join(stream_ops) + "\n").encode("latin-1")
        content_id = add_obj(f"<< /Length {len(content_data)} >>\nstream\n{content_data.decode('latin-1')}endstream")
        page_id = add_obj(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {w_pt:.2f} {h_pt:.2f}] /Contents {content_id} 0 R >>"
        )
        page_ids.append(page_id)

    kids_str = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects[pages_placeholder_idx] = f"<< /Type /Pages /Kids [{kids_str}] /Count {len(page_ids)} >>".encode("latin-1")

    buf = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = [0]
    for i, obj_bytes in enumerate(objects, start=1):
        offsets.append(len(buf))
        buf.extend(f"{i} 0 obj\n".encode("latin-1"))
        buf.extend(obj_bytes)
        buf.extend(b"\nendobj\n")

    xref_pos = len(buf)
    buf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    buf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        buf.extend(f"{off:010d} 00000 n \n".encode("latin-1"))

    buf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("latin-1")
    )
    target.write_bytes(bytes(buf))
    return target