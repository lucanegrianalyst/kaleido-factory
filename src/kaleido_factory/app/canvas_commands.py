"""Parser comandi testuali e conversione preset per il canvas interattivo."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from kaleido_factory.app.pipeline import CompositionConfig
from kaleido_factory.core.document import MarginsSpec, PageSpec
from kaleido_factory.effects.presets import PresetSpec, list_presets, load_preset, save_preset
from kaleido_factory.layout.formats import make_book_page


HELP_TEXT = (
    "Comandi: sectors <n> | mirror <on|off> | effect <none|neon|shading|writing> | "
    "echo <n> [scale stroke] | spacing <px> | width <px> | smooth <p> [w] | subdiv <i> [r] | "
    "center <x> <y> | page <fmt> [orient] | grid <r> <c> [gutter] | budget <full_quality|fast_preview> | "
    "save_preset <nome> | load_preset <nome> | presets | undo | clear | export <svg|png|pdf> [dir]"
)


def _preset_from_config(name: str, cfg: CompositionConfig) -> PresetSpec:
    return PresetSpec(
        name=name,
        sectors=cfg.sectors,
        mirror=cfg.mirror,
        smoothing_passes=cfg.smoothing_passes,
        subdivisions=cfg.subdivisions,
        echo_count=cfg.echo_count,
        scale_step=cfg.scale_step,
        stroke_step=cfg.stroke_step,
        effects=cfg.effects,
    )


def _apply_preset_to_config(preset: PresetSpec, cfg: CompositionConfig) -> CompositionConfig:
    return replace(
        cfg,
        sectors=preset.sectors,
        mirror=preset.mirror,
        smoothing_passes=preset.smoothing_passes,
        subdivisions=preset.subdivisions,
        echo_count=preset.echo_count,
        scale_step=preset.scale_step,
        stroke_step=preset.stroke_step,
        effects=preset.effects,
    )


def parse_command(
    line: str,
    cfg: CompositionConfig,
    *,
    page: PageSpec | None = None,
    rows: int = 1,
    cols: int = 1,
    gutter_pt: float = 12.0,
    budget_mode: str = "full_quality",
    presets_dir: Path | None = None,
) -> tuple[CompositionConfig, str, str | None]:
    """Analizza un comando testuale e restituisce (nuova_config, messaggio, azione_speciale)."""
    _ = (page, rows, cols, budget_mode)
    raw = line.strip()
    if not raw:
        return cfg, HELP_TEXT, None

    parts = raw.split()
    cmd = parts[0].lower()
    args = parts[1:]
    p_dir = presets_dir if presets_dir is not None else Path("presets")

    if cmd == "help":
        return cfg, HELP_TEXT, None
    if cmd == "undo":
        return cfg, "Annullato ultimo tratto.", "undo"
    if cmd == "clear":
        return cfg, "Canvas svuotato.", "clear"
    if cmd == "sectors" and len(args) == 1:
        return replace(cfg, sectors=int(args[0])), f"Settori impostati a {int(args[0])}.", None
    if cmd == "mirror" and len(args) == 1 and args[0].lower() in ("on", "off", "true", "false", "1", "0"):
        flag = args[0].lower() in ("on", "true", "1")
        return replace(cfg, mirror=flag), f"Specchio {'attivo' if flag else 'disattivato'}.", None
    if cmd == "effect" and len(args) == 1:
        eff_name = args[0].lower()
        effects = () if eff_name in ("none", "off", "base") else (eff_name,)
        return replace(cfg, effects=effects), f"Effetto impostato: {eff_name}.", None
    if cmd == "echo" and len(args) in (1, 3):
        count = int(args[0])
        if len(args) == 3:
            return (
                replace(cfg, echo_count=count, scale_step=float(args[1]), stroke_step=float(args[2])),
                f"Eco: {count} (scala={float(args[1])}, tratto={float(args[2])}).",
                None,
            )
        return replace(cfg, echo_count=count), f"Linee eco impostate a {count}.", None
    if cmd == "spacing" and len(args) == 1:
        return replace(cfg, spacing=float(args[0])), f"Spaziatura impostata a {float(args[0])}.", None
    if cmd == "width" and len(args) == 1:
        return replace(cfg, base_stroke_width=float(args[0])), f"Spessore base impostato a {float(args[0])}.", None
    if cmd == "smooth" and len(args) in (1, 2):
        passes = int(args[0])
        weight = float(args[1]) if len(args) == 2 else cfg.smoothing_weight
        return replace(cfg, smoothing_passes=passes, smoothing_weight=weight), f"Smoothing: {passes} passate (peso={weight}).", None
    if cmd == "subdiv" and len(args) in (1, 2):
        iters = int(args[0])
        ratio = float(args[1]) if len(args) == 2 else cfg.corner_ratio
        return replace(cfg, subdivisions=iters, corner_ratio=ratio), f"Suddivisione: {iters} iterazioni (ratio={ratio}).", None
    if cmd == "center" and len(args) == 2:
        cx, cy = float(args[0]), float(args[1])
        return replace(cfg, center=(cx, cy)), f"Centro simmetria impostato a ({cx:.1f}, {cy:.1f}).", None
    if cmd == "budget" and len(args) == 1 and args[0].lower() in ("full_quality", "fast_preview"):
        mode = args[0].lower()
        return cfg, f"Budget condiviso (preview+export): {mode}.", f"set_budget:{mode}"
    if cmd == "page" and len(args) in (1, 2):
        orient = args[1].lower() if len(args) == 2 else "portrait"
        new_page = make_book_page(args[0], orientation=orient, margins=MarginsSpec(36, 36, 36, 36))
        return cfg, f"Pagina: {args[0]} ({orient}).", f"set_page:{args[0]}:{orient}"
    if cmd == "grid" and len(args) in (2, 3):
        r_val, c_val = int(args[0]), int(args[1])
        g_val = float(args[2]) if len(args) == 3 else gutter_pt
        if r_val < 1 or c_val < 1 or g_val < 0:
            raise ValueError("Parametri griglia non validi.")
        return cfg, f"Griglia: {r_val}x{c_val} (gutter={g_val}pt).", f"set_grid:{r_val}:{c_val}:{g_val}"
    if cmd == "save_preset" and len(args) == 1:
        spec = _preset_from_config(args[0], cfg)
        path = save_preset(spec, p_dir)
        return cfg, f"Preset '{args[0]}' salvato in {path}.", None
    if cmd == "load_preset" and len(args) == 1:
        spec = load_preset(args[0], p_dir)
        return _apply_preset_to_config(spec, cfg), f"Preset '{spec.name}' caricato.", None
    if cmd == "presets" and len(args) == 0:
        names = list_presets(p_dir)
        label = ", ".join(names) if names else "(nessuno)"
        return cfg, f"Preset disponibili: {label}", None
    if cmd == "export" and len(args) in (1, 2):
        fmt = args[0].lower()
        target = args[1] if len(args) == 2 else str(Path("output/canvas_export"))
        return cfg, f"Esportazione {fmt} verso {target}...", f"export:{fmt}:{target}"

    raise ValueError(f"Comando non riconosciuto o argomenti non validi: '{raw}'")