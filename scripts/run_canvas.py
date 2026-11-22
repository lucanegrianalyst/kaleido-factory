"""Avvio rapido del canvas interattivo a comandi di kaleido_factory."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from kaleido_factory.app.interactive_canvas import launch_interactive_canvas


if __name__ == "__main__":
    launch_interactive_canvas()