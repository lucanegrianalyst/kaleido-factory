"""Test per effects/stroke_styles.py e effects/presets.py."""

from __future__ import annotations

from pathlib import Path
import pytest

from kaleido_factory.effects.presets import PresetSpec, list_presets, load_preset, save_preset
from kaleido_factory.effects.stroke_styles import build_neon_layers, build_shading_strokes, modulate_writing_stroke


def test_neon_shading_and_writing_effects() -> None:
    line = [(0.0, 0.0), (20.0, 0.0), (40.0, 10.0)]

    neon = build_neon_layers(line, core_width=2.0, glow_steps=2)
    assert len(neon) == 3
    assert neon[-1].role == "neon_core"
    assert neon[0].width > neon[-1].width

    shaded = build_shading_strokes(line, base_width=1.5, hatch_length=5.0, hatch_step=1)
    assert len(shaded) == 4
    assert shaded[0].role == "base"
    assert shaded[1].role == "shading_hatch"

    written = modulate_writing_stroke(line, base_width=2.0, taper=0.3)
    assert len(written) == 2
    assert all(s.role == "writing_seg" for s in written)


def test_preset_save_load_and_list(tmp_path: Path) -> None:
    preset = PresetSpec(
        name="mandala_01",
        sectors=8,
        mirror=True,
        smoothing_passes=2,
        subdivisions=2,
        echo_count=3,
        effects=("neon", "shading"),
    )
    saved_path = save_preset(preset, tmp_path)
    assert saved_path.is_file()
    assert list_presets(tmp_path) == ["mandala_01"]

    loaded = load_preset("mandala_01", tmp_path)
    assert loaded == preset

    with pytest.raises(ValueError):
        PresetSpec(name="../bad_name")