---
ticket_schema: 1
ticket_id: "DBH-28"
execution_mode: AFK
blocked_by: []
---

# DBH-28 — Unità di giudizio, alberi ricostruiti e robustezza

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:28`
- Role: `ticket`
- Parent: [delivery-bench-hard-quality-judge.md](../../specs/delivery-bench-hard-quality-judge.md)

## Parent Spec
[delivery-bench-hard-quality-judge.md](../../specs/delivery-bench-hard-quality-judge.md)

## What to Build
`quality.py units --lot L` elenca ogni richiesta: lotto, cella, braccio, scenario, richiesta, stato, base, albero e diff.

Materializza l'albero di ogni richiesta in una cartella dal nome neutro. Usa come alternates `diffs/objects`, `snapshot/project/.git/objects` e `snapshot/origin.git/objects`.

`quality.py report` scrive `quality/report.md` e `report.json`. Per braccio e scenario riporta l'accettazione ufficiale, `axes.robustness` e `axes.compass`. Le colonne delle altre misure restano vuote finché mancano.

Spec: Target behavior 1, 2 e 6.

## Acceptance Criteria
- [ ] Compaiono tutte le richieste dei lotti, comprese quelle senza diff ("nessun codice").
- [ ] L'albero materializzato coincide con `diff.tree`: `git write-tree` dà lo stesso oid.
- [ ] Lo script non scrive fuori da `results/<lot>/quality/`; `cell.json` e il ledger restano identici byte per byte.

## Frontier
Ready.

## Gates
Come la spec:
- un tentativo è un giudizio completo di `dbh-luna3d` più `dbh-luna3e`;
- nessun tetto di budget né di tempo, con la spesa riportata;
- al massimo 2 tentativi, il pilota e il giudizio completo;
- nessuna versione esatta;
- merge con CI 8/8 e `--match-head-commit`.

Blocco: niente esecuzioni Docker o Opus sui lotti veri finché `dbh-luna3e` gira.

## Step-by-Step Implementation Plan
1. Leggere `lot.json` e `cells/*/cell.json`.
2. Materializzare l'albero con `git archive`, da un repository vuoto con gli alternates.
3. Scrivere il report in Markdown e JSON, con mediana e quartili.

## Testing Plan
- `python -B -m unittest test_quality`, su un lotto giocattolo creato dal test.
- Smoke su `dbh-luna3d` in sola lettura, senza Docker.

## Out of Scope
- Copertura, mutation e revisione (DBH-29, DBH-30, DBH-31).
