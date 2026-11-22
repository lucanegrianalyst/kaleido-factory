"""Formati editoriali, orientamenti (portrait, landscape, square) e calcolo area utile."""

from __future__ import annotations

from dataclasses import dataclass

from kaleido_factory.core.document import MarginsSpec, PageSpec
from kaleido_factory.core.units import Orientation, POINTS_PER_INCH, inches_to_points


@dataclass(frozen=True)
class PrintableRect:
    """Rettangolo utile interno ai margini espresso in punti tipografici (72 pt/in)."""

    x_pt: float
    y_pt: float
    width_pt: float
    height_pt: float


BOOK_FORMAT_PRESETS: dict[str, tuple[float, float]] = {
    "book_6x9": (6.0, 9.0),
    "book_5x8": (5.0, 8.0),
    "book_85x11": (8.5, 11.0),
    "book_a4": (8.27, 11.69),
    "book_square_85": (8.5, 8.5),
}


def make_book_page(
    preset_name: str,
    *,
    orientation: Orientation = "portrait",
    margins: MarginsSpec | None = None,
) -> PageSpec:
    """Crea una PageSpec da un formato editoriale predefinito."""
    if not isinstance(preset_name, str) or preset_name.strip() not in BOOK_FORMAT_PRESETS:
        valid = ", ".join(sorted(BOOK_FORMAT_PRESETS))
        raise ValueError(f"Formato non supportato '{preset_name}'. Formati validi: {valid}")
    w_in, h_in = BOOK_FORMAT_PRESETS[preset_name.strip()]
    eff_margins = MarginsSpec() if margins is None else margins
    return PageSpec(width_inches=w_in, height_inches=h_in, orientation=orientation, margins=eff_margins)


def compute_printable_rect(page: PageSpec) -> PrintableRect:
    """Calcola l'area stampabile interna ai margini in punti tipografici."""
    if not isinstance(page, PageSpec):
        raise TypeError("page deve essere un'istanza di PageSpec.")
    m = page.margins
    w_pt = page.width_inches * POINTS_PER_INCH
    h_pt = page.height_inches * POINTS_PER_INCH
    inner_w = w_pt - (m.left + m.right)
    inner_h = h_pt - (m.top + m.bottom)
    if inner_w <= 0.0 or inner_h <= 0.0:
        raise ValueError("L'area stampabile residua deve essere positiva.")
    return PrintableRect(x_pt=m.left, y_pt=m.top, width_pt=inner_w, height_pt=inner_h)


def inches_box_to_points(width_inches: float, height_inches: float) -> tuple[float, float]:
    """Converte larghezza e altezza in pollici in punti tipografici."""
    return (inches_to_points(width_inches), inches_to_points(height_inches))