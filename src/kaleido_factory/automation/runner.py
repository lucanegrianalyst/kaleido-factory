"""Esecutore di azioni di automazione con supporto dry_run, validazione e log esiti."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from kaleido_factory.automation.actions import (
    ActionRecord,
    BatchExportAction,
    ExportTrigger,
    MouseDriver,
    MouseMoveAction,
    NoopMouseDriver,
)

AutomationAction = MouseMoveAction | BatchExportAction


@dataclass(frozen=True)
class AutomationResult:
    """Risultato complessivo di una sequenza di azioni."""

    records: tuple[ActionRecord, ...]
    halted_on_error: bool = False

    @property
    def ok_count(self) -> int:
        return sum(1 for r in self.records if r.status == "ok")

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.records if r.status == "error")


def run_automation_actions(
    actions: Sequence[AutomationAction],
    *,
    mouse_driver: MouseDriver | None = None,
    export_trigger: ExportTrigger | None = None,
    dry_run: bool = True,
    stop_on_error: bool = True,
) -> AutomationResult:
    """Esegue in sequenza azioni di cursore ed export restituendo un registro immutabile."""
    if not isinstance(dry_run, bool):
        raise TypeError("dry_run deve essere booleano.")
    if not isinstance(stop_on_error, bool):
        raise TypeError("stop_on_error deve essere booleano.")

    driver: MouseDriver = NoopMouseDriver() if mouse_driver is None else mouse_driver
    records: list[ActionRecord] = []
    halted = False

    for act in actions:
        try:
            if isinstance(act, MouseMoveAction):
                if not dry_run:
                    driver.move_to(act.x, act.y, duration_sec=act.duration_sec)
                records.append(
                    ActionRecord(
                        action_type="mouse_move",
                        status="ok",
                        detail=f"({act.x:.2f}, {act.y:.2f}) dur={act.duration_sec:.2f}s",
                        dry_run=dry_run,
                    )
                )
            elif isinstance(act, BatchExportAction):
                if not dry_run:
                    if export_trigger is None:
                        raise RuntimeError("export_trigger richiesto quando dry_run=False.")
                    written = export_trigger.trigger_export(act.output_path, fmt=act.fmt, dpi=act.dpi)
                    detail = f"{act.fmt} -> {written}"
                else:
                    detail = f"[dry-run] {act.fmt} -> {act.output_path}"
                records.append(
                    ActionRecord(
                        action_type="batch_export",
                        status="ok",
                        detail=detail,
                        dry_run=dry_run,
                    )
                )
            else:
                raise TypeError(f"Azione non supportata: {type(act).__name__}")
        except Exception as exc:  # noqa: BLE001
            records.append(
                ActionRecord(
                    action_type=type(act).__name__,
                    status="error",
                    detail=str(exc),
                    dry_run=dry_run,
                )
            )
            if stop_on_error:
                halted = True
                break

    return AutomationResult(records=tuple(records), halted_on_error=halted)