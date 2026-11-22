"""Test dedicati al modulo kaleido_factory.app.pipeline."""

from __future__ import annotations

import importlib


def test_module_imports_and_exposes_symbols() -> None:
    mod = importlib.import_module("kaleido_factory.app.pipeline")
    public_attrs = [name for name in dir(mod) if not name.startswith("_")]
    assert len(public_attrs) > 0