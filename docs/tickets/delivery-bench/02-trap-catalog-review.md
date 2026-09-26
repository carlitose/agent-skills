---
ticket_schema: 1
ticket_id: "DB-02"
execution_mode: HITL
blocked_by:
  - "DB-01"
---

# DB-02 — Catalogo delle trappole di memoria, revisione umana

## Artifact Graph
- Artifact ID: `ticket:delivery-bench:02`
- Role: `ticket`
- Parent: [delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## Parent Spec
[delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## What to Build
Preparare per ciascuno dei tre scenari il catalogo concreto delle trappole (deprecato, decisione architetturale, bug chiuso, contratto, convenzione): in quale richiesta si pianta la regola, in quale richiesta arriva la tentazione, distanza, controllo nascosto che la rileva. Poi un'intervista (`grilling`) con l'utente che approva o cambia il catalogo. Sezione della mappa: Decision 8, Decision 10.

## Acceptance Criteria
- [ ] Catalogo per scenario con almeno una trappola per tipo, distanze diverse (1, 3, 5+ richieste) e il controllo nascosto associato.
- [ ] L'utente ha approvato il catalogo nell'intervista; le modifiche richieste sono applicate e registrate.
- [ ] Il catalogo non rivela ai bracci nulla: resta nel repo privato del benchmark.

## Frontier
Bloccato da DB-01. Decisione umana richiesta: approvazione del catalogo.

## Step-by-Step Implementation Plan
1. Redigere il catalogo per scenario.
2. Intervista con l'utente, una domanda alla volta.
3. Registrare la versione approvata nel repo privato.

## Testing Plan
Revisione umana; nessun test automatico oltre la coerenza del catalogo con il contratto DB-01.

## Out of Scope
- Scrivere le suite (DB-03/04/05).
