# Guida Pagina, Slot e Spazio Coordinate (`CanvasPageSpace`)

- **`src/kaleido_factory/app/canvas_page_space.py`**: definisce la mappatura tra coordinate canvas (`px`) e coordinate reali di pagina/slot (`pt`) per qualunque formato (`PageSpec`) e griglia (`rows`, `cols`, `gutter_pt`), senza rimpicciolire tratti che escono dal foglio o dallo slot.
- **`src/kaleido_factory/app/canvas_page_overlay.py`**: disegna il bordo del foglio e degli slot usando il tag isolato `page_guide` (attivabile/disattivabile con `guide on` / `guide off`).
- **`src/kaleido_factory/app/facade.py`**: allinea i tratti alle coordinate locali dello slot (`pt`) mantenendo le proporzioni reali.
