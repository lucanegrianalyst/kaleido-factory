"""Impaginazione multi-disegno con griglie, margini paginati e posizionamento condiviso."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from kaleido_factory.core.document import PageSpec
from kaleido_factory.core.validation import require_finite_float, require_int
from kaleido_factory.layout.formats import PrintableRect, compute_printable_rect


@dataclass(frozen=True)
class PlacedSlot:
    """Posizione e dimensione (in punti) di un singolo disegno dentro una pagina."""

    item_index: int
    page_index: int
    slot_index: int
    x_pt: float
    y_pt: float
    width_pt: float
    height_pt: float


@dataclass(frozen=True)
class LayoutPage:
    """Singola pagina impaginata con i riquadri posizionati."""

    page_index: int
    page: PageSpec
    printable: PrintableRect
    slots: tuple[PlacedSlot, ...]


@dataclass(frozen=True)
class PaginatedLayout:
    """Documento impaginato su una o piu pagine."""

    pages: tuple[LayoutPage, ...]

    @property
    def total_pages(self) -> int:
        return len(self.pages)


def paginate_items(
    item_count: int,
    *,
    page: PageSpec,
    rows: int = 1,
    cols: int = 1,
    gutter_pt: float = 12.0,
    preserve_aspect: bool = True,
    item_aspect_ratios: Sequence[float] | None = None,
) -> PaginatedLayout:
    """Distribuisce item_count disegni su pagine a griglia rows x cols con margini e gutter."""
    count = require_int(item_count, "item_count", min_value=0)
    n_rows = require_int(rows, "rows", min_value=1)
    n_cols = require_int(cols, "cols", min_value=1)
    gutter = require_finite_float(gutter_pt, "gutter_pt", allow_zero=True)
    if not isinstance(preserve_aspect, bool):
        raise TypeError("preserve_aspect deve essere booleano.")
    if not isinstance(page, PageSpec):
        raise TypeError("page deve essere un'istanza di PageSpec.")

    printable = compute_printable_rect(page)
    total_gap_x = gutter * (n_cols - 1)
    total_gap_y = gutter * (n_rows - 1)
    cell_w = (printable.width_pt - total_gap_x) / n_cols
    cell_h = (printable.height_pt - total_gap_y) / n_rows
    if cell_w <= 0.0 or cell_h <= 0.0:
        raise ValueError("Le celle della griglia risultano non positive: riduci margini, righe, colonne o gutter.")

    if count == 0:
        return PaginatedLayout(pages=())

    per_page = n_rows * n_cols
    num_pages = (count + per_page - 1) // per_page
    pages_out: list[LayoutPage] = []

    for p_idx in range(num_pages):
        start = p_idx * per_page
        end = min(count, start + per_page)
        page_slots: list[PlacedSlot] = []

        for local_idx in range(end - start):
            item_idx = start + local_idx
            r = local_idx // n_cols
            c = local_idx % n_cols
            box_x = printable.x_pt + c * (cell_w + gutter)
            box_y = printable.y_pt + r * (cell_h + gutter)

            w_out, h_out = cell_w, cell_h
            x_out, y_out = box_x, box_y

            if preserve_aspect and item_aspect_ratios is not None and item_idx < len(item_aspect_ratios):
                ar = require_finite_float(item_aspect_ratios[item_idx], f"aspect_ratio[{item_idx}]", positive_only=True)
                cell_ar = cell_w / cell_h
                if ar > cell_ar:
                    h_out = cell_w / ar
                    y_out = box_y + 0.5 * (cell_h - h_out)
                else:
                    w_out = cell_h * ar
                    x_out = box_x + 0.5 * (cell_w - w_out)

            page_slots.append(
                PlacedSlot(
                    item_index=item_idx,
                    page_index=p_idx,
                    slot_index=local_idx,
                    x_pt=x_out,
                    y_pt=y_out,
                    width_pt=w_out,
                    height_pt=h_out,
                )
            )

        pages_out.append(
            LayoutPage(
                page_index=p_idx,
                page=page,
                printable=printable,
                slots=tuple(page_slots),
            )
        )

    return PaginatedLayout(pages=tuple(pages_out))