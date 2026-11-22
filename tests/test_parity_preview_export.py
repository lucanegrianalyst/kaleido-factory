"""Test di parità 1:1 tra tratti calcolati per preview ed esportazione."""

from __future__ import annotations

from pathlib import Path

from kaleido_factory.app.facade import build_all_styled_strokes, compose_and_paginate, export_composition_bundle
from kaleido_factory.app.pipeline import CompositionConfig
from kaleido_factory.core.cache import ParameterCache
from kaleido_factory.core.document import MarginsSpec
from kaleido_factory.core.point_budget import BudgetConfig
from kaleido_factory.layout.formats import make_book_page


def test_preview_and_export_produce_identical_strokes(tmp_path: Path) -> None:
    polys = [
        [(10.0, 10.0), (40.0, 20.0), (25.0, 55.0)],
        [(15.0, 30.0), (50.0, 15.0), (35.0, 60.0)],
    ]
    cfg = CompositionConfig(
        sectors=8,
        mirror=True,
        center=(30.0, 30.0),
        echo_count=2,
        effects=("shading",),
    )
    budget = BudgetConfig(mode="full_quality")
    cache = ParameterCache(max_entries=64)
    page = make_book_page("book_6x9", orientation="portrait", margins=MarginsSpec(36, 36, 36, 36))

    preview_strokes = build_all_styled_strokes(polys, config=cfg, budget_config=budget, cache=cache)
    layout, export_strokes = compose_and_paginate(
        polys,
        page=page,
        rows=1,
        cols=2,
        config=cfg,
        budget_config=budget,
        cache=cache,
    )
    assert preview_strokes == export_strokes
    assert layout.total_pages == 1

    bundle = export_composition_bundle(
        polys,
        tmp_path / "parity_out",
        page=page,
        rows=1,
        cols=2,
        dpi=72,
        include_pdf=True,
        config=cfg,
        budget_config=budget,
        cache=cache,
    )
    assert bundle.pdf_file is not None and bundle.pdf_file.is_file()