---
ticket_schema: 1
ticket_id: "TBA-03"
execution_mode: AFK
blocked_by:
  - "TBA-02"
  - "TBA-07"
---

# TBA-03 — Report appaiato e scelta del vincitore

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-best-arm:03`
- Role: `ticket`
- Parent: [terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## Parent Spec
[terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## What to Build
Confrontare i quattro bracci — Pi bare (lotto B), skills-only (TBA-02), c1a e c3a generici (TBA-07) — task per task, ciascuno contro Pi bare, con la regola della spec: se la differenza è di al massimo 3 task o McNemar esatto dà p ≥ 0,05, eseguire una ripetizione in più per entrambi i bracci prima di decidere, altrimenti a parità vince il braccio più semplice. Committare report, vincitore e split dev/held-out deterministico. Sezioni spec: Decisions 3–4.

## Acceptance Criteria
- [ ] La tabella appaiata copre gli stessi 63 task; le eccezioni senza voto contano come fallimento e sono contate a parte.
- [ ] Il report riporta il p-value McNemar calcolato e la decisione secondo la regola, senza pesi soggettivi.
- [ ] La split dev(42)/held-out(21) è derivata dall'ordinamento SHA-256 dei nomi task e committata prima di qualsiasi modifica all'agente.

## Frontier
Bloccato da TBA-02 e TBA-07.

## Step-by-Step Implementation Plan
1. Ridurre i due ledger e i result.json in una tabella appaiata.
2. Applicare la regola; se serve, eseguire la ripetizione extra di entrambi i bracci.
3. Scrivere report e split; PR e merge.

## Testing Plan
Ricalcolo deterministico della tabella dai file sorgente; test unitario della funzione McNemar e della split.

## Out of Scope
- Sviluppo del vincitore (TBA-04).
- Confronti su harness modificato.
