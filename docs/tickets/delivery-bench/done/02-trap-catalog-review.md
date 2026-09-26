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
- [x] Catalogo per scenario con almeno una trappola per tipo, distanze diverse (1, 3, 5+ richieste) e il controllo nascosto associato.
- [x] L'utente ha approvato il catalogo nell'intervista; le modifiche richieste sono applicate e registrate.
- [x] Il catalogo non rivela ai bracci nulla: resta nel repo privato del benchmark.

## Frontier
**Completato** (2026-09-26, skills-only): catalogo nel repo privato locale dell'oracolo (`dbench-private/catalog.md`, commit `56540d0`, sha256 `67c2d576…`), mai in questo repo. Conteggio: 9 trappole per Python, 9 per C, 12 per TypeScript/Svelte; tutti e cinque i tipi in ogni scenario; distanze 1-6; due trappole per scenario con tentazione entro la richiesta 3, così la catena da 3 le misura. Intervista `grilling` (4 domande): domini e sequenze approvati, una seconda trappola a distanza 1-2 aggiunta per scenario su richiesta dell'utente, latenti invariati, catalogo approvato.

## Step-by-Step Implementation Plan
1. Redigere il catalogo per scenario.
2. Intervista con l'utente, una domanda alla volta.
3. Registrare la versione approvata nel repo privato.

## Testing Plan
Revisione umana; nessun test automatico oltre la coerenza del catalogo con il contratto DB-01.

## Out of Scope
- Scrivere le suite (DB-03/04/05).
