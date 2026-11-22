"""Modello dati immutabile condiviso per layout, geometria, effetti ed export."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping, Sequence

from kaleido_factory.core.units import (
    Orientation,
    POINTS_PER_INCH,
    aspect_ratio,
    inches_to_points,
    resolve_dimensions,
)
from kaleido_factory.core.validation import (
    Point2D,
    require_finite_float,
    validate_points,
)


def _validate_color(color: object, field_name: str) -> str:
    if not isinstance(color, str) or not color.strip():
        raise ValueError(f"{field_name} deve essere una stringa colore non vuota.")
    return color.strip()


@dataclass(frozen=True)
class MarginsSpec:
    """Margini di pagina in punti tipografici (72 pt/in)."""

    top: float = 36.0
    right: float = 36.0
    bottom: float = 36.0
    left: float = 36.0

    def __post_init__(self) -> None:
        for side in ("top", "right", "bottom", "left"):
            val = require_finite_float(getattr(self, side), f"margins.{side}", allow_zero=True)
            object.__setattr__(self, side, val)


@dataclass(frozen=True)
class PageSpec:
    """Dimensioni fisiche pagina (in/pt), orientamento e margini."""

    width_inches: float
    height_inches: float
    orientation: Orientation = "portrait"
    margins: MarginsSpec = field(default_factory=MarginsSpec)

    def __post_init__(self) -> None:
        resolved_w, resolved_h = resolve_dimensions(self.width_inches, self.height_inches, self.orientation)
        if not isinstance(self.margins, MarginsSpec):
            raise TypeError("margins deve essere un'istanza di MarginsSpec.")
        width_pt = inches_to_points(resolved_w)
        height_pt = inches_to_points(resolved_h)
        if self.margins.left + self.margins.right >= width_pt:
            raise ValueError("I margini orizzontali superano o eguagliano la larghezza pagina.")
        if self.margins.top + self.margins.bottom >= height_pt:
            raise ValueError("I margini verticali superano o eguagliano l'altezza pagina.")
        object.__setattr__(self, "width_inches", resolved_w)
        object.__setattr__(self, "height_inches", resolved_h)

    @property
    def width_points(self) -> float:
        return self.width_inches * POINTS_PER_INCH

    @property
    def height_points(self) -> float:
        return self.height_inches * POINTS_PER_INCH

    @property
    def aspect_ratio(self) -> float:
        return aspect_ratio(self.width_inches, self.height_inches)


@dataclass(frozen=True)
class CoordinateSystemSpec:
    """Sistema di coordinate geometriche e controllo del rapporto d'aspetto."""

    width: float
    height: float
    aspect_tolerance: float = 1e-3

    def __post_init__(self) -> None:
        w = require_finite_float(self.width, "coord.width", positive_only=True)
        h = require_finite_float(self.height, "coord.height", positive_only=True)
        tol = require_finite_float(self.aspect_tolerance, "coord.aspect_tolerance", allow_zero=True)
        object.__setattr__(self, "width", w)
        object.__setattr__(self, "height", h)
        object.__setattr__(self, "aspect_tolerance", tol)

    @property
    def aspect_ratio(self) -> float:
        return aspect_ratio(self.width, self.height)

    def matches_page_aspect(self, page: PageSpec) -> bool:
        if not isinstance(page, PageSpec):
            raise TypeError("page deve essere un'istanza di PageSpec.")
        return math.isclose(self.aspect_ratio, page.aspect_ratio, rel_tol=self.aspect_tolerance, abs_tol=self.aspect_tolerance)


@dataclass(frozen=True)
class PolylineItem:
    """Singola polilinea o disegno con spessore positivo finito ed effetti opzionali."""

    points: tuple[Point2D, ...]
    stroke_width: float = 1.5
    stroke_color: str | None = None
    closed: bool = False
    effects: tuple[str, ...] = ()
    metadata: Mapping[str, float | int | str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.closed, bool):
            raise TypeError("closed deve essere booleano.")
        validated = tuple(validate_points(list(self.points), min_points=2, allow_degenerate=True))
        width = require_finite_float(self.stroke_width, "polyline.stroke_width", positive_only=True)
        color = None if self.stroke_color is None else _validate_color(self.stroke_color, "polyline.stroke_color")
        if not isinstance(self.effects, Sequence) or isinstance(self.effects, (str, bytes)):
            raise TypeError("effects deve essere una sequenza di nomi effetto.")
        clean_effects = tuple(_validate_color(e, "polyline.effects[]") for e in self.effects)
        object.__setattr__(self, "points", validated)
        object.__setattr__(self, "stroke_width", width)
        object.__setattr__(self, "stroke_color", color)
        object.__setattr__(self, "effects", clean_effects)


@dataclass(frozen=True)
class FrameSpec:
    """Cornice del disegno/pagina con spessore nullo o positivo finito e colore."""

    width: float = 0.0
    color: str = "#000000"

    def __post_init__(self) -> None:
        w = require_finite_float(self.width, "frame.width", allow_zero=True)
        c = _validate_color(self.color, "frame.color")
        object.__setattr__(self, "width", w)
        object.__setattr__(self, "color", c)


@dataclass(frozen=True)
class DocumentSpec:
    """Documento condiviso immutabile pronto per anteprima, layout ed export."""

    page: PageSpec
    coordinates: CoordinateSystemSpec
    polylines: tuple[PolylineItem, ...] = ()
    stroke_color: str = "#111111"
    background_color: str = "#FFFFFF"
    frame: FrameSpec = field(default_factory=FrameSpec)
    enforce_aspect_match: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.page, PageSpec):
            raise TypeError("page deve essere un'istanza di PageSpec.")
        if not isinstance(self.coordinates, CoordinateSystemSpec):
            raise TypeError("coordinates deve essere un'istanza di CoordinateSystemSpec.")
        if not isinstance(self.enforce_aspect_match, bool):
            raise TypeError("enforce_aspect_match deve essere booleano.")
        if not isinstance(self.polylines, Sequence) or isinstance(self.polylines, (str, bytes)):
            raise TypeError("polylines deve essere una sequenza di PolylineItem.")
        for idx, item in enumerate(self.polylines):
            if not isinstance(item, PolylineItem):
                raise TypeError(f"polylines[{idx}] deve essere un'istanza di PolylineItem.")
        if not isinstance(self.frame, FrameSpec):
            raise TypeError("frame deve essere un'istanza di FrameSpec.")

        sc = _validate_color(self.stroke_color, "stroke_color")
        bg = _validate_color(self.background_color, "background_color")
        if self.enforce_aspect_match and not self.coordinates.matches_page_aspect(self.page):
            raise ValueError("Il rapporto d'aspetto delle coordinate non corrisponde a quello della pagina.")

        object.__setattr__(self, "polylines", tuple(self.polylines))
        object.__setattr__(self, "stroke_color", sc)
        object.__setattr__(self, "background_color", bg)