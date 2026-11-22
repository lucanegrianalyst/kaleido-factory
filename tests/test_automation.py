"""Test per automation/actions.py e automation/runner.py."""

from __future__ import annotations

from pathlib import Path
import pytest

from kaleido_factory.automation.actions import (
    BatchExportAction,
    MemoryExportTrigger,
    MouseMoveAction,
    NoopMouseDriver,
)
from kaleido_factory.automation.runner import run_automation_actions


def test_automation_dry_run_and_live_execution(tmp_path: Path) -> None:
    out_file = tmp_path / "sheet_001.svg"
    actions = [
        MouseMoveAction(120.0, 240.0, duration_sec=0.1),
        BatchExportAction(out_file, fmt="svg", dpi=150),
    ]

    dry_res = run_automation_actions(actions, dry_run=True)
    assert dry_res.ok_count == 2
    assert dry_res.error_count == 0
    assert all(r.dry_run is True for r in dry_res.records)

    mouse = NoopMouseDriver()
    exporter = MemoryExportTrigger(create_file=True)
    live_res = run_automation_actions(actions, mouse_driver=mouse, export_trigger=exporter, dry_run=False)

    assert live_res.ok_count == 2
    assert len(mouse.moves) == 1
    assert len(exporter.exports) == 1
    assert out_file.is_file()


def test_automation_missing_trigger_halts_on_error(tmp_path: Path) -> None:
    actions = [
        BatchExportAction(tmp_path / "out.png", fmt="png", dpi=150),
        MouseMoveAction(10.0, 20.0),
    ]
    res = run_automation_actions(actions, dry_run=False, stop_on_error=True)
    assert res.halted_on_error is True
    assert res.error_count == 1
    assert len(res.records) == 1

    with pytest.raises(ValueError):
        BatchExportAction(tmp_path / "bad.xyz", fmt="xyz")