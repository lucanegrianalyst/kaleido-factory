# Guida Pagina e Slot sul Canvas

Il modulo `src/kaleido_factory/app/canvas_page_overlay.py` mostra sul canvas un riferimento proporzionato di **pagina** e **slot di impaginazione** (`PlacedSlot`), così puoi valutare l'ingombro del disegno rispetto all'esportazione.

## Caratteristiche architetturali
- **Scollegabile**: non altera la geometria dei tratti né il flusso di `export_composition_bundle`. Tutti gli elementi grafici usano il tag `page_guide` e vengono rimossi/ridisegnati in isolamento.
- **Modificabile e divisibile**: il calcolo geometrico (`compute_page_guide_layout`) è separato dal rendering Tkinter (`draw_page_guide`).

## Comandi
- `guide on` — mostra i contorni di pagina e slot.
- `guide off` — nasconde i contorni guida.
- `page <fmt> [orient]` / `grid <r> <c> [gutter]` — aggiorna in tempo reale la guida al formato e alla griglia correnti.
