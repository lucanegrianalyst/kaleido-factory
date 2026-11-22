"""Contratti sostituibili e strutture dati per azioni di automazione (mouse e export)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from kaleido_factory.core.validation import require_finite_float, require_int


@runtime_checkable
class MouseDriver(Protocol):
    """Contratto sostituibile per il controllo del cursore."""

    def move_to(self, x: float, y: float, *, duration_sec: float = 0.0) -> None:
        """Sposta il cursore alle coordinate (x, y)."""


@runtime_checkable
class ExportTrigger(Protocol):
    """Contratto sostituibile per avviare salvataggio o esportazione automatica."""

    def trigger_export(self, target_path: Path, *, fmt: str = "svg", dpi: int = 150) -> Path:
        """Esegue l'esportazione verso target_path e restituisce il percorso scritto."""


@dataclass(frozen=True)
class MouseMoveAction:
    """Comando di spostamento cursore validato."""

    x: float
    y: float
    duration_sec: float = 0.0

    def __post_init__(self) -> None:
        px = require_finite_float(self.x, "x")
        py = require_finite_float(self.y, "y")
        dur = require_finite_float(self.duration_sec, "duration_sec", allow_zero=True)
        object.__setattr__(self, "x", px)
        object.__setattr__(self, "y", py)
        object.__setattr__(self, "duration_sec", dur)


@dataclass(frozen=True)
class BatchExportAction:
    """Comando di salvataggio/esportazione automatica validato."""

    output_path: Path
    fmt: str = "svg"
    dpi: int = 150

    def __post_init__(self) -> None:
        if not isinstance(self.output_path, (Path, str)) or not str(self.output_path).strip():
            raise ValueError("output_path deve essere un percorso non vuoto.")
        clean_fmt = str(self.fmt).strip().lower()
        if clean_fmt not in ("svg", "png", "pdf"):
            raise ValueError(f"Formato di export non supportato: {self.fmt}")
        valid_dpi = require_int(self.dpi, "dpi", min_value=36)
        object.__setattr__(self, "output_path", Path(self.output_path))
        object.__setattr__(self, "fmt", clean_fmt)
        object.__setattr__(self, "dpi", valid_dpi)


@dataclass(frozen=True)
class ActionRecord:
    """Esito registrato di una singola azione eseguita o simulata."""

    action_type: str
    status: str
    detail: str
    dry_run: bool


class NoopMouseDriver:
    """Driver cursore sicuro in memoria per test e dry-run."""

    def __init__(self) -> None:
        self.moves: list[tuple[float, float, float]] = []

    def move_to(self, x: float, y: float, *, duration_sec: float = 0.0) -> None:
        self.moves.append((float(x), float(y), float(duration_sec)))


class MemoryExportTrigger:
    """Trigger di export in memoria/disco per test e integrazione."""

    def __init__(self, *, create_file: bool = False) -> None:
        self.create_file = bool(create_file)
        self.exports: list[tuple[Path, str, int]] = []

    def trigger_export(self, target_path: Path, *, fmt: str = "svg", dpi: int = 150) -> Path:
        dest = Path(target_path)
        self.exports.append((dest, fmt, dpi))
        if self.create_file:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(f"# exported {fmt} ({dpi} dpi)\n", encoding="utf-8")
        return dest