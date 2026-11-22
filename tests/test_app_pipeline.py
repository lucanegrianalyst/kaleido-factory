"""Test end-to-end per app/pipeline.py e app/facade.py."""

from __future__ import annotations

from pathlib import Path

from kaleido_factory.app.facade import compose_and_paginate, export_composition_bundle
from kaleido_factory.app.pipeline import CompositionConfig, build_styled_strokes
from kaleido_factory.core.cache import ParameterCache
from kaleido_factory.core.document import MarginsSpec
from kaleido_factory.core.point_budget import BudgetConfig
from kaleido_factory.layout.formats import make_book_page


def test_pipeline_parity_and_cache() -> None:
    poly = [(10.0, 0.0), (25.0, 12.0), (15.0, 30.0)]
    cfg = CompositionConfig(sectors=6, mirror=True, echo_count=2, effects=("neon",))
    cache = ParameterCache(max_entries=32)

    s1 = build_styled_strokes(poly, config=cfg, budget_config=BudgetConfig(mode="full_quality"), cache=cache)
    s2 = build_styled_strokes(poly, config=cfg, budget_config=BudgetConfig(mode="full_quality"), cache=cache)
    assert len(s1) > 0 and s1 == s2
    assert cache.size == 1


def test_compose_paginate_and_export_bundle(tmp_path: Path) -> None:
    polys = [
        [(5.0, 5.0), (20.0, 10.0), (12.0, 25.0)],
        [(8.0, 2.0), (18.0, 18.0), (4.0, 22.0)],
    ]
    page = make_book_page("book_6x9", orientation="portrait", margins=MarginsSpec(36, 36, 36, 36))
    layout, strokes = compose_and_paginate(polys, page=page, rows=1, cols=2)
    assert layout.total_pages == 1 and len(strokes) == 2

    bundle = export_composition_bundle(polys, tmp_path / "out", page=page, rows=1, cols=2, dpi=72, include_pdf=True)
    assert len(bundle.svg_files) == 1 and bundle.svg_files[0].is_file()
    assert len(bundle.png_files) == 1 and bundle.png_files[0].is_file()
    assert bundle.pdf_file is not None and bundle.pdf_file.is_file()