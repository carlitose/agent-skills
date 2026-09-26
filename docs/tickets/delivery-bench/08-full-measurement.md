---
ticket_schema: 1
ticket_id: "DB-08"
execution_mode: HITL
blocked_by:
  - "DB-07"
---

# DB-08 — Misura completa: catene da 3 e 8

## Artifact Graph
- Artifact ID: `ticket:delivery-bench:08`
- Role: `ticket`
- Parent: [delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## Parent Spec
[delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## What to Build
Eseguire le catene da 3 (3 ripetizioni) e da 8 (1 ripetizione) per i cinque bracci nei tre scenari, poi il report finale: tabella braccio × lunghezza × scenario sui cinque assi e la raccomandazione operativa («per task da N richieste usa X»), con i limiti dichiarati.

## Acceptance Criteria
- [ ] Nuova autorizzazione esplicita dell'utente con tetto di tempo per catena.
- [ ] Tutte le celle con profilo; le ripetizioni extra della catena da 8 solo dove la regola di TBA-03 lo richiede.
- [ ] Report finale con raccomandazione e limiti; nessun numero unico.

## Frontier
Bloccato da DB-07 e da una nuova autorizzazione.

## Step-by-Step Implementation Plan
1. Autorizzazione.
2. Catene da 3, poi da 8.
3. Report finale.

## Testing Plan
Live.

## Out of Scope
- Migliorare i bracci nello stesso lotto.
