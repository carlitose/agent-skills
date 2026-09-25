---
ticket_schema: 1
ticket_id: "TBA-04"
execution_mode: AFK
blocked_by:
  - "TBA-03"
---

# TBA-04 — Sviluppare il braccio vincitore senza adattarsi al benchmark

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-best-arm:04`
- Role: `ticket`
- Parent: [terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## Parent Spec
[terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## What to Build
Migliorare il vincitore usando solo traiettorie e verifier dei task dev: tassonomia dei fallimenti, piccole modifiche mirate (system prompt, contenuto delle skill, ergonomia del tool sandbox, abitudini di verifica e stop), rilancio dev, poi una misura held-out e una completa. Sezioni spec: Decision 4, Invariants.

## Acceptance Criteria
- [ ] Ogni modifica è motivata da fallimenti dev citati; nessun log del verifier held-out è letto prima della misura finale.
- [ ] Una modifica è accettata solo se migliora dev e non peggiora held-out rispetto al vincitore di TBA-03.
- [ ] Il report finale separa i risultati dev, held-out e 63-task e cita ogni lotto; ci si ferma dopo tre iterazioni dev senza guadagno superiore a 2 task.

## Frontier
Bloccato da TBA-03.

## Step-by-Step Implementation Plan
1. Tassonomia dei fallimenti dev dalle traiettorie.
2. Iterazioni: modifica, test offline, lotto dev.
3. Misura held-out e completa; report; PR e merge.

## Testing Plan
Test offline per ogni modifica dell'adapter; lotti live dev/held-out con ledger propri.

## Out of Scope
- Nuovi modelli, task GPU, pubblicazione su leaderboard.
