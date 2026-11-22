"""Canvas interattivo a comandi con parità 1:1 tra visualizzazione realtime ed export."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk

from kaleido_factory.app.canvas_commands import HELP_TEXT, parse_command
from kaleido_factory.app.canvas_page_overlay import draw_page_guide
from kaleido_factory.app.canvas_page_space import CanvasPageSpace, build_canvas_page_space
from kaleido_factory.app.facade import build_all_styled_strokes, export_composition_bundle
from kaleido_factory.app.pipeline import CompositionConfig
from kaleido_factory.core.cache import ParameterCache
from kaleido_factory.core.document import MarginsSpec, PageSpec
from kaleido_factory.core.point_budget import BudgetConfig
from kaleido_factory.core.validation import Point2D
from kaleido_factory.effects.stroke_styles import StyledStroke
from kaleido_factory.layout.formats import make_book_page


class InteractiveKaleidoApp:
    """Finestra di disegno con riga comandi e parità visiva 1:1 tra preview ed export."""

    def __init__(self, root: tk.Tk, *, width: int = 920, height: int = 640) -> None:
        self.root = root
        self.root.title("Kaleido Factory - Canvas a Comandi (1:1 Preview/Export)")
        self.strokes_raw: list[list[Point2D]] = []
        self.current_stroke: list[Point2D] = []
        self.cfg = CompositionConfig(center=(width / 2.0, (height - 76) / 2.0))
        self.page: PageSpec = make_book_page("book_6x9", orientation="portrait", margins=MarginsSpec(36, 36, 36, 36))
        self.rows: int = 1
        self.cols: int = 1
        self.gutter_pt: float = 12.0
        self.show_page_guide: bool = True
        self._space: CanvasPageSpace = build_canvas_page_space(self.page, canvas_width=width, canvas_height=height - 76, rows=self.rows, cols=self.cols, gutter_pt=self.gutter_pt)
        self.budget_cfg = BudgetConfig(mode="full_quality")
        self.presets_dir: Path = Path("presets")
        self.history: list[str] = []
        self.history_idx: int = 0
        self.cache = ParameterCache(max_entries=128)
        self.last_rendered_strokes: list[tuple[StyledStroke, ...]] = []

        self.canvas = tk.Canvas(
            root,
            width=width,
            height=height - 76,
            bg="#ffffff",
            highlightthickness=1,
            highlightbackground="#cccccc",
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        bottom = ttk.Frame(root, padding=6)
        bottom.pack(fill=tk.X)

        self.status_var = tk.StringVar(value=HELP_TEXT)
        ttk.Label(bottom, textvariable=self.status_var, wraplength=width - 20).pack(anchor=tk.W)

        cmd_row = ttk.Frame(bottom)
        cmd_row.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(cmd_row, text="Comando >").pack(side=tk.LEFT, padx=(0, 6))
        self.cmd_entry = ttk.Entry(cmd_row)
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.cmd_entry.bind("<Return>", lambda _e: self._execute_from_entry())
        self.cmd_entry.bind("<Up>", lambda _e: self._step_history(-1))
        self.cmd_entry.bind("<Down>", lambda _e: self._step_history(1))
        ttk.Button(cmd_row, text="Esegui", command=self._execute_from_entry).pack(side=tk.LEFT, padx=(6, 0))

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.cmd_entry.focus_set()

    def _active_polylines(self) -> list[list[Point2D]]:
        polys = list(self.strokes_raw)
        if len(self.current_stroke) >= 2:
            polys.append(self.current_stroke)
        return polys

    def _on_press(self, event: tk.Event) -> None:
        self.current_stroke = [(float(event.x), float(event.y))]
        self.redraw()

    def _on_motion(self, event: tk.Event) -> None:
        self.current_stroke.append((float(event.x), float(event.y)))
        self.redraw()

    def _on_release(self, event: tk.Event) -> None:
        self.current_stroke.append((float(event.x), float(event.y)))
        if len(self.current_stroke) >= 2:
            self.strokes_raw.append(self.current_stroke)
        self.current_stroke = []
        self.redraw()

    def _step_history(self, delta: int) -> str:
        if not self.history:
            return "break"
        new_idx = max(0, min(len(self.history), self.history_idx + delta))
        self.history_idx = new_idx
        self.cmd_entry.delete(0, tk.END)
        if new_idx < len(self.history):
            self.cmd_entry.insert(0, self.history[new_idx])
        return "break"

    def _apply_special(self, special: str | None) -> None:
        if not special:
            return
        if special == "undo" and self.strokes_raw:
            self.strokes_raw.pop()
        elif special == "clear":
            self.strokes_raw.clear()
            self.current_stroke.clear()
        elif special.startswith("set_budget:"):
            _, mode = special.split(":", 1)
            self.budget_cfg = BudgetConfig(mode=mode)
        elif special.startswith("set_page:"):
            _, fmt_name, orient = special.split(":", 2)
            self.page = make_book_page(fmt_name, orientation=orient, margins=MarginsSpec(36, 36, 36, 36))
        elif special.startswith("set_guide:"):
            _, flag_s = special.split(":", 1)
            self.show_page_guide = flag_s == "1"
        elif special.startswith("set_grid:"):
            _, r_s, c_s, g_s = special.split(":", 3)
            self.rows, self.cols, self.gutter_pt = int(r_s), int(c_s), float(g_s)
        elif special.startswith("export:"):
            _, fmt, target = special.split(":", 2)
            self._run_export(fmt, Path(target))

    def _execute_from_entry(self) -> None:
        line = self.cmd_entry.get()
        self.cmd_entry.delete(0, tk.END)
        if line.strip():
            self.history.append(line.strip())
            self.history_idx = len(self.history)
        try:
            new_cfg, msg, special = parse_command(
                line,
                self.cfg,
                page=self.page,
                rows=self.rows,
                cols=self.cols,
                gutter_pt=self.gutter_pt,
                budget_mode=self.budget_cfg.mode,
                presets_dir=self.presets_dir,
            )
            self.cfg = new_cfg
            self._apply_special(special)
            if special and special.startswith("export:"):
                _, fmt, target = special.split(":", 2)
                exported_count = self._count_exported_files(Path(target), fmt)
                msg = f"Esportato ({fmt}, {exported_count} file) in {target} [1:1 preview/export]."
            eff_label = ",".join(self.cfg.effects) if self.cfg.effects else "base"
            mirror_label = "on" if self.cfg.mirror else "off"
            summary = f" | [sec={self.cfg.sectors} mir={mirror_label} eff={eff_label} tratti={len(self.strokes_raw)}]"
            self.status_var.set(msg + summary)
            self.redraw()
        except Exception as exc:  # noqa: BLE001
            self.status_var.set(f"[Errore comando] {exc}")

    def _count_exported_files(self, out_dir: Path, fmt: str) -> int:
        if not out_dir.exists():
            return 0
        exts = {".svg", ".png", ".pdf"} if fmt == "pdf" else {".svg", ".png"}
        return sum(1 for p in out_dir.iterdir() if p.is_file() and p.suffix.lower() in exts)

    def _run_export(self, fmt: str, out_dir: Path) -> None:
        all_polys = self._active_polylines()
        if not all_polys:
            raise ValueError("Nessun tratto da esportare.")
        slot_polys = [
            self._space.canvas_points_to_slot_local_pt(poly, slot_index=0)
            for poly in all_polys
        ]
        slot_center = self._space.canvas_points_to_slot_local_pt(
            [self.cfg.center], slot_index=0
        )[0]
        export_cfg = replace(self.cfg, center=slot_center)
        export_composition_bundle(
            slot_polys,
            out_dir,
            page=self.page,
            rows=self.rows,
            cols=self.cols,
            gutter_pt=self.gutter_pt,
            dpi=150,
            include_pdf=(fmt == "pdf"),
            config=export_cfg,
            budget_config=self.budget_cfg,
            cache=self.cache,
        )

    def _draw_styled_stroke(self, st: StyledStroke) -> None:
        if len(st.points) < 2:
            return
        coords = [coord for pt in st.points for coord in pt]
        color = "#0088cc" if st.role.startswith("neon") else "#111111"
        self.canvas.create_line(*coords, fill=color, width=max(1.0, st.width), smooth=False)

    def redraw(self) -> None:
        self.canvas.delete("all")
        cw = float(self.canvas.winfo_width() or self.canvas.cget("width"))
        ch = float(self.canvas.winfo_height() or self.canvas.cget("height"))
        self._space = build_canvas_page_space(
            self.page,
            canvas_width=cw,
            canvas_height=ch,
            rows=self.rows,
            cols=self.cols,
            gutter_pt=self.gutter_pt,
        )
        if self.show_page_guide:
            draw_page_guide(self.canvas, self._space)
        cx, cy = self.cfg.center
        self.canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill="#cc3333", outline="")

        styled_list = build_all_styled_strokes(
            self._active_polylines(),
            config=self.cfg,
            budget_config=self.budget_cfg,
            cache=self.cache,
        )
        self.last_rendered_strokes = styled_list
        for styled in styled_list:
            for st in styled:
                self._draw_styled_stroke(st)


def launch_interactive_canvas() -> None:
    """Avvia la finestra interattiva di disegno a comandi."""
    root = tk.Tk()
    InteractiveKaleidoApp(root)
    root.mainloop()