"""Test per il parser comandi del canvas interattivo (parametri, preset, impaginazione)."""

from __future__ import annotations

from pathlib import Path
import pytest

from kaleido_factory.app.canvas_commands import parse_command
from kaleido_factory.app.pipeline import CompositionConfig


def test_parse_canvas_commands_and_presets(tmp_path: Path) -> None:
    presets_dir = tmp_path / "presets"
    cfg = CompositionConfig(sectors=6, mirror=True, echo_count=0)

    cfg, _, _ = parse_command("sectors 8", cfg, presets_dir=presets_dir)
    assert cfg.sectors == 8

    cfg, _, _ = parse_command("effect neon", cfg, presets_dir=presets_dir)
    assert cfg.effects == ("neon",)

    cfg, _, _ = parse_command("echo 2 0.85 0.9", cfg, presets_dir=presets_dir)
    assert cfg.echo_count == 2 and cfg.scale_step == pytest.approx(0.85)

    _, msg_save, _ = parse_command("save_preset mandala_8", cfg, presets_dir=presets_dir)
    assert "mandala_8" in msg_save

    reset_cfg = CompositionConfig(sectors=4, mirror=False, echo_count=0)
    loaded_cfg, _, _ = parse_command("load_preset mandala_8", reset_cfg, presets_dir=presets_dir)
    assert loaded_cfg.sectors == 8
    assert loaded_cfg.echo_count == 2
    assert loaded_cfg.effects == ("neon",)

    _, _, page_act = parse_command("page book_6x9 landscape", loaded_cfg, presets_dir=presets_dir)
    assert page_act == "set_page:book_6x9:landscape"

    _, _, grid_act = parse_command("grid 2 2 14.0", loaded_cfg, presets_dir=presets_dir)
    assert grid_act == "set_grid:2:2:14.0"

    with pytest.raises(ValueError):
        parse_command("comando_inesistente", loaded_cfg, presets_dir=presets_dir)