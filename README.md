# Kaleido Factory

Motore modulare in Python per generare composizioni geometriche simmetriche, impaginarle su formati pagina/griglia ed esportarle in **SVG**, **PNG** e **PDF** con parita' visiva 1:1 rispetto all'anteprima interattiva.

## Avvio rapido

Dal root del progetto (`C:\kaleido_factory`):

- Avvio canvas: `python .\scripts\run_canvas.py`
- Test e controlli: `.\scripts\07_run_checks.ps1`

## Struttura del codice (`src/kaleido_factory`)

- `core/`: unita', validazione, cache, point budget e modello documento.
- `geometry/`: preparazione curva, ricampionamento, smoothing, suddivisione, simmetria ed echo lines.
- `effects/`: stili del tratto e preset salvabili su disco.
- `layout/`: formati pagina e impaginazione/griglie.
- `rendering/`: esportatori SVG e PNG/PDF.
- `automation/`: azioni e runner per flussi automatizzati.
- `app/`: pipeline, facade, comandi e canvas interattivo (`1:1 Preview/Export`).

## Comandi principali nel Canvas

- `sectors <n>` - imposta il numero di settori radiali
- `mirror <on|off>` - attiva o disattiva la simmetria speculare
- `effect <none|neon|shading|writing>` - seleziona l'effetto visivo
- `echo <n> [scale] [stroke]` - configura le linee eco
- `page <fmt> [orient]` e `grid <r> <c> [gutter]` - imposta formato pagina e griglia
- `save_preset <name>` / `load_preset <name>` / `presets` - gestisce i preset
- `undo` / `clear` - annulla l'ultimo tratto o svuota il foglio
- `export <svg|png|pdf> [dir]` - esporta il risultato

## Regole di scalabilita' e manutenzione

- Mantenere la gerarchia a strati (`core` in basso, `geometry`/`effects`/`layout` al centro, `rendering`/`automation`/`app` in alto) evitando dipendenze circolari.
- Mantenere ogni modulo sorgente `<= 250` righe.
- Associare a ogni nuovo modulo in `src/kaleido_factory` il relativo file `tests/test_<modulo>.py`.
