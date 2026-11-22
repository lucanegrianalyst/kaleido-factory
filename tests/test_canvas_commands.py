from __future__ import annotations

from pathlib import Path
import pytest

from kaleido_factory.app.canvas_commands import parse_command
from kaleido_factory.app.pipeline import CompositionConfig


def test_parse_command_updates_sectors_and_mirror() -> None:
    cfg = CompositionConfig()
    cfg2, msg1, err1 = parse_command("sectors 8", cfg)
    assert err1 is None and cfg2.sectors == 8 and "8" in msg1

    cfg3, msg2, err2 = parse_command("mirror off", cfg2)
    assert err2 is None and cfg3.mirror is False and msg2


def test_parse_command_unknown_raises_value_error() -> None:
    cfg = CompositionConfig()
    with pytest.raises(ValueError):
        parse_command("comando_inesistente", cfg)


def test_export_command_uses_project_output_root() -> None:
    cfg = CompositionConfig()
    _, _, special = parse_command("export pdf", cfg)
    assert special is not None and special.startswith("export:pdf:")
    target = Path(special.split(":", 2)[2])
    assert target.is_absolute()
    assert target.parts[-2:] == ("output", "canvas_export")
