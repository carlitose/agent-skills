---
type: source
title: "DB-02 — Catalogo delle trappole di memoria, revisione umana"
identity_key: ticket:delivery-bench/DB-02
identity_strength: stable
source_path: docs/tickets/delivery-bench/done/02-trap-catalog-review.md
source_digest: sha256:c3b4baf688f6b7974fb9cbb523855122b360bd28482fa59bb372f203ff78f389
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-26
created_provenance: git-commit
disposition_changed: 2026-09-26
disposition_changed_provenance: git-rename
---

# DB-02 — Catalogo delle trappole di memoria, revisione umana

Compiled from `docs/tickets/delivery-bench/done/02-trap-catalog-review.md`. Identity is `ticket:delivery-bench/DB-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-26** via `git-commit`
- Disposition changed: **2026-09-26** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-bench]]
- Blocked by: [[sources/ticket-delivery-bench-db-01]] — `ticket:delivery-bench/DB-01`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-db-02.md","payload_bytes":2111,"payload_sha256":"c3b4baf688f6b7974fb9cbb523855122b360bd28482fa59bb372f203ff78f389"}],"payload_bytes":2111,"payload_sha256":"c3b4baf688f6b7974fb9cbb523855122b360bd28482fa59bb372f203ff78f389","schema":1,"source_digest":"sha256:c3b4baf688f6b7974fb9cbb523855122b360bd28482fa59bb372f203ff78f389","source_identity":"ticket:delivery-bench/DB-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2111,"payload_sha256":"c3b4baf688f6b7974fb9cbb523855122b360bd28482fa59bb372f203ff78f389","schema":1,"source_digest":"sha256:c3b4baf688f6b7974fb9cbb523855122b360bd28482fa59bb372f203ff78f389","source_identity":"ticket:delivery-bench/DB-02"} -->
```markdown
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

```
