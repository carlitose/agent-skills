---
ticket_schema: 1
ticket_id: "DB-06"
execution_mode: AFK
blocked_by:
  - "DB-01"
---

# DB-06 — Runner dei bracci e report a profilo

## Artifact Graph
- Artifact ID: `ticket:delivery-bench:06`
- Role: `ticket`
- Parent: [delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## Parent Spec
[delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## What to Build
Un comando unico per braccio × scenario × lunghezza che: consegna la richiesta N al braccio nel suo modo naturale, attende la consegna, esegue la suite nascosta della richiesta N, passa alla N+1; registra token, USD stimati (Jev a parte), tempo, e produce il profilo a cinque assi. Report deterministico e confronto appaiato con la regola di TBA-03 (`arm_comparison.py`). Ripetizioni e ledger come nei lotti Terminal-Bench (autorità, ledger fuori da Git, guasti d'infrastruttura ripetuti).

## Acceptance Criteria
- [ ] Il comando esegue una catena completa per un braccio con processi finti e scrive il profilo per richiesta; test offline RED→GREEN.
- [ ] Ogni braccio gira nel suo modo naturale (una sessione per Pi nudo e skills-only; driver per ticket; Autopilot con runner) e riceve la richiesta N+1 solo dopo la consegna della N.
- [ ] Il report riporta i cinque assi senza numero unico, la distanza delle trappole violate e i guasti d'infrastruttura classificati e ripetuti.
- [ ] Un tetto di tempo per catena termina il braccio e conserva il profilo parziale.

## Frontier
Bloccato da DB-01.

## Step-by-Step Implementation Plan
1. Test RED con bracci finti.
2. Runner, ledger, classificatore riusati da Terminal-Bench.
3. Report e confronto appaiato.

## Testing Plan
Offline con bracci finti; una catena da 1 reale in DB-07.

## Out of Scope
- Scrivere scenari.
- Migliorare i bracci.
