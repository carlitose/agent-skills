---
ticket_schema: 1
ticket_id: "TDC-01"
execution_mode: AFK
blocked_by: []
---

# TDC-01 — Le cache degli strumenti non sono scritture del revisore diretto

## Artifact Graph
- Artifact ID: `ticket:ticket-driver-reviewer-tool-caches:01`
- Role: `ticket`
- Parent: [ticket-driver-reviewer-tool-caches.md](../../specs/ticket-driver-reviewer-tool-caches.md)

## Parent Spec
[ticket-driver-reviewer-tool-caches.md](../../specs/ticket-driver-reviewer-tool-caches.md)

## What to Build
In `ticket-driver/scripts/risk.py`, `directed_review` esclude dal controllo delle scritture le
cartelle di cache degli strumenti (`TOOL_CACHES`) e il loro contenuto, e le registra
nell'evento `directed-tool-caches`. Ogni altro percorso nella scratch ferma il run come prima.
La foglia finta dei test lascia queste cache, e in un secondo modo anche un file proprio.

## Acceptance Criteria
- [x] Un revisore che lascia `.pytest_cache` e `__pycache__` nella scratch integra, e il ledger
  registra le due cache. Prima della correzione il run si ferma con
  `directed reviewer wrote outside artifact`.
- [x] Un revisore che lascia le cache e un file proprio resta fermo, e l'evento della violazione
  elenca solo il file. Prima della correzione elenca anche le cache.
- [x] Il test esistente sulla scrittura relativa nel prodotto resta verde, con l'intera suite di
  `ticket-driver`.

## Outcome
2026-10-01. I due test nuovi falliscono prima della correzione e passano dopo, con l'intera suite
di `ticket-driver`.

## Frontier
Chiuso. Vale da una nuova `prepare-drivers`; le copie del lotto `dbh-opus` non cambiano.

## Step-by-Step Implementation Plan
1. Test RED in `test_c3.py` e due modi nuovi della foglia finta.
2. `TOOL_CACHES` e `_tool_cache` in `risk.py`, usati dal controllo delle scritture.
3. Suite di `ticket-driver`.

## Testing Plan
`python -B -m unittest discover -s tests` da `ticket-driver`.

## Out of Scope
- La cartella di lavoro del revisore e i comandi che può eseguire.
- Le cache nella worktree del candidato.
