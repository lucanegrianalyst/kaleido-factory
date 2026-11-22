"""Validazioni rigorose su numeri, interi/booleani, DPI, percorsi e punti."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable, Sequence

Point2D = tuple[float, float]


def require_finite_float(
    value: object,
    name: str,
    *,
    allow_zero: bool = True,
    positive_only: bool = False,
) -> float:
    """Valida un numero reale finito escludendo esplicitamente i booleani."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} deve essere un numero reale (non booleano).")
    num = float(value)
    if not math.isfinite(num):
        raise ValueError(f"{name} deve essere un valore finito.")
    if positive_only and num <= 0.0:
        raise ValueError(f"{name} deve essere maggiore di zero.")
    if not allow_zero and num == 0.0:
        raise ValueError(f"{name} non puo essere zero.")
    if num < 0.0:
        raise ValueError(f"{name} non puo essere negativo.")
    return num


def require_signed_finite_float(value: object, name: str) -> float:
    """Valida un numero reale finito anche negativo (es. coordinate)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} deve essere un numero reale (non booleano).")
    num = float(value)
    if not math.isfinite(num):
        raise ValueError(f"{name} deve essere un valore finito.")
    return num


def require_int(value: object, name: str, *, min_value: int | None = None, max_value: int | None = None) -> int:
    """Valida un intero escludendo esplicitamente i booleani."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} deve essere un intero (non booleano).")
    if min_value is not None and value < min_value:
        raise ValueError(f"{name} deve essere >= {min_value}.")
    if max_value is not None and value > max_value:
        raise ValueError(f"{name} deve essere <= {max_value}.")
    return value


def validate_dpi(dpi: object, allowed_dpis: Sequence[int] = (72, 96, 150, 300, 600)) -> int:
    """Valida il DPI per export raster, escludendo booleani e valori non ammessi."""
    val = require_int(dpi, "dpi", min_value=1)
    if val not in allowed_dpis:
        raise ValueError(f"DPI {val} non ammesso. Valori ammessi: {list(allowed_dpis)}")
    return val


def strip_known_extensions(base_path: str | Path, extensions: Iterable[str] = (".svg", ".png", ".pdf")) -> Path:
    """Rimuove eventuali estensioni gia presenti alla fine del percorso."""
    path = Path(base_path)
    normalized_exts = {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions}
    current = path
    while current.suffix.lower() in normalized_exts:
        current = current.with_suffix("")
    return current


def validate_points(
    points: Sequence[Point2D],
    *,
    min_points: int = 0,
    allow_degenerate: bool = True,
    degenerate_eps: float = 1e-12,
) -> list[Point2D]:
    """Valida una sequenza di punti 2D finiti e controlla eventuali segmenti degeneri."""
    if not isinstance(points, Sequence) or isinstance(points, (str, bytes)):
        raise TypeError("points deve essere una sequenza di coppie (x, y).")
    if len(points) < min_points:
        raise ValueError(f"Servono almeno {min_points} punti; ricevuti {len(points)}.")

    cleaned: list[Point2D] = []
    for idx, pt in enumerate(points):
        if not isinstance(pt, Sequence) or isinstance(pt, (str, bytes)) or len(pt) != 2:
            raise ValueError(f"Punto all'indice {idx} non valido: attesa coppia (x, y).")
        x = require_signed_finite_float(pt[0], f"points[{idx}].x")
        y = require_signed_finite_float(pt[1], f"points[{idx}].y")
        cleaned.append((x, y))

    if not allow_degenerate and len(cleaned) >= 2:
        for i in range(1, len(cleaned)):
            if math.hypot(cleaned[i][0] - cleaned[i - 1][0], cleaned[i][1] - cleaned[i - 1][1]) <= degenerate_eps:
                raise ValueError(f"Segmento degenere rilevato tra i punti {i - 1} e {i}.")

    return cleaned

def require_dpi(value: object, name: str = "dpi", *, min_value: int = 36, max_value: int = 1200) -> int:
    """Valida una risoluzione DPI come intero positivo (non booleano) entro un intervallo sicuro."""
    dpi = require_int(value, name, min_value=min_value)
    max_dpi = require_int(max_value, "max_value", min_value=min_value)
    if dpi > max_dpi:
        raise ValueError(f"{name} non puo superare {max_dpi} (ricevuto: {dpi}).")
    return dpi
