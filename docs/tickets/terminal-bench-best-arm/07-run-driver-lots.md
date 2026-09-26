---
ticket_schema: 1
ticket_id: "TBA-07"
execution_mode: AFK
blocked_by:
  - "TBA-06"
  - "TBA-02"
---

# TBA-07 — Lotti c1a e c3a sui 63 task originali

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-best-arm:07`
- Role: `ticket`
- Parent: [terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## Parent Spec
[terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## What to Build
Eseguire una ripetizione dei 63 task (GPU esclusi) per c1a e poi per c3a, con la stessa policy flat-rate, `-n 3` e `no_network_docker` di skills-only, in serie dopo TBA-02, e ripetere le celle fallite per infrastruttura. Sezione spec: Decisions 1–3, Generic ticket-driver arms.

## Acceptance Criteria
- [ ] Lot, authority e ledger propri per braccio, fuori da Git, vincolati alla head integrata di TBA-06.
- [ ] Ogni cella avviata al più una volta nel lotto principale; le celle `infra:*` ripetute in lotti separati, al massimo due volte; intenti originali intatti.
- [ ] Per ogni cella restano result.json di Harbor, ricevuta, journal modello e Jev, fasi eseguite, verdetto e correzione.

## Frontier
Bloccato da TBA-06 e dalla fine di TBA-02.

## Step-by-Step Implementation Plan
1. Attendere la chiusura di TBA-02 senza container attivi.
2. Lotto c1a, retry infra; lotto c3a, retry infra.
3. Riassunto grezzo per TBA-03.

## Testing Plan
Controlli live su ledger, journal e result.json; classificazione con `retry_classification.py`.

## Out of Scope
- Modifiche all'agente durante i lotti.
- Task GPU o ripetizioni extra.
