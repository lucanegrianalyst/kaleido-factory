"""Salvataggio, caricamento e validazione di preset geometrici/stile nominati."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from kaleido_factory.core.validation import require_int


_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def validate_preset_name(name: object) -> str:
    """Verifica che il nome del preset sia sicuro e privo di separatori di percorso."""
    if not isinstance(name, str) or not _SAFE_NAME_RE.match(name.strip()):
        raise ValueError("Nome preset non valido: usa solo lettere, numeri, '_' o '-' (max 64 caratteri).")
    return name.strip()


@dataclass(frozen=True)
class PresetSpec:
    """Configurazione nominata riutilizzabile per simmetria, eco, smoothing e stile."""

    name: str
    sectors: int = 6
    mirror: bool = True
    smoothing_passes: int = 1
    subdivisions: int = 1
    echo_count: int = 0
    scale_step: float = 0.85
    stroke_step: float = 0.85
    effects: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        clean_name = validate_preset_name(self.name)
        sec = require_int(self.sectors, "sectors", min_value=1)
        if not isinstance(self.mirror, bool):
            raise TypeError("mirror deve essere booleano.")
        sm = require_int(self.smoothing_passes, "smoothing_passes", min_value=0)
        sd = require_int(self.subdivisions, "subdivisions", min_value=0)
        ec = require_int(self.echo_count, "echo_count", min_value=0)
        clean_fx = tuple(str(x).strip() for x in self.effects if str(x).strip())
        object.__setattr__(self, "name", clean_name)
        object.__setattr__(self, "sectors", sec)
        object.__setattr__(self, "smoothing_passes", sm)
        object.__setattr__(self, "subdivisions", sd)
        object.__setattr__(self, "echo_count", ec)
        object.__setattr__(self, "effects", clean_fx)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "sectors": self.sectors,
            "mirror": self.mirror,
            "smoothing_passes": self.smoothing_passes,
            "subdivisions": self.subdivisions,
            "echo_count": self.echo_count,
            "scale_step": self.scale_step,
            "stroke_step": self.stroke_step,
            "effects": list(self.effects),
        }


def save_preset(preset: PresetSpec, directory: Path | str) -> Path:
    """Salva un preset in formato JSON UTF-8 senza BOM nella cartella indicata."""
    if not isinstance(preset, PresetSpec):
        raise TypeError("preset deve essere un'istanza di PresetSpec.")
    target_dir = Path(directory)
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / f"{preset.name}.json"
    out_path.write_text(json.dumps(preset.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def load_preset(name: str, directory: Path | str) -> PresetSpec:
    """Carica e valida un preset nominato dalla cartella indicata."""
    clean_name = validate_preset_name(name)
    file_path = Path(directory) / f"{clean_name}.json"
    if not file_path.is_file():
        raise FileNotFoundError(f"Preset non trovato: {file_path}")
    raw = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Il file preset deve contenere un oggetto JSON.")
    return PresetSpec(
        name=raw.get("name", clean_name),
        sectors=raw.get("sectors", 6),
        mirror=raw.get("mirror", True),
        smoothing_passes=raw.get("smoothing_passes", 1),
        subdivisions=raw.get("subdivisions", 1),
        echo_count=raw.get("echo_count", 0),
        scale_step=raw.get("scale_step", 0.85),
        stroke_step=raw.get("stroke_step", 0.85),
        effects=tuple(raw.get("effects", ())),
    )


def list_presets(directory: Path | str) -> list[str]:
    """Restituisce i nomi ordinati dei preset disponibili nella cartella."""
    target_dir = Path(directory)
    if not target_dir.is_dir():
        return []
    names: list[str] = []
    for p in sorted(target_dir.glob("*.json")):
        try:
            names.append(validate_preset_name(p.stem))
        except ValueError:
            continue
    return names