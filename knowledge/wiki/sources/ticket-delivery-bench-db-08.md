---
type: source
title: "DB-08 — Misura completa: catene da 3 e 8"
identity_key: ticket:delivery-bench/DB-08
identity_strength: stable
source_path: docs/tickets/delivery-bench/done/08-full-measurement.md
source_digest: sha256:dabdae248d7a1a10f1b4205bc162d3f48f7c3600dc52ddb82eea104544ff6919
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-27
created_provenance: git-commit
disposition_changed: 2026-09-27
disposition_changed_provenance: git-rename
---

# DB-08 — Misura completa: catene da 3 e 8

Compiled from `docs/tickets/delivery-bench/done/08-full-measurement.md`. Identity is `ticket:delivery-bench/DB-08`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-27** via `git-commit`
- Disposition changed: **2026-09-27** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-bench]]
- Child source: [[sources/artifact-delivery-bench-results]]
- Blocked by: [[sources/ticket-delivery-bench-db-07]] — `ticket:delivery-bench/DB-07`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[5],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[4],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-db-08.md","payload_bytes":2515,"payload_sha256":"dabdae248d7a1a10f1b4205bc162d3f48f7c3600dc52ddb82eea104544ff6919"}],"payload_bytes":2515,"payload_sha256":"dabdae248d7a1a10f1b4205bc162d3f48f7c3600dc52ddb82eea104544ff6919","schema":1,"source_digest":"sha256:dabdae248d7a1a10f1b4205bc162d3f48f7c3600dc52ddb82eea104544ff6919","source_identity":"ticket:delivery-bench/DB-08","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 4: What to Build |
| acceptance | 5: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2515,"payload_sha256":"dabdae248d7a1a10f1b4205bc162d3f48f7c3600dc52ddb82eea104544ff6919","schema":1,"source_digest":"sha256:dabdae248d7a1a10f1b4205bc162d3f48f7c3600dc52ddb82eea104544ff6919","source_identity":"ticket:delivery-bench/DB-08"} -->
```markdown
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

### Produces
- [delivery-bench-results.md](../../research/delivery-bench-results.md)

## Parent Spec
[delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## What to Build
Eseguire le catene da 3 (3 ripetizioni) e da 8 (1 ripetizione) per i cinque bracci nei tre scenari, poi il report finale: tabella braccio × lunghezza × scenario sui cinque assi e la raccomandazione operativa («per task da N richieste usa X»), con i limiti dichiarati.

## Acceptance Criteria
- [x] Nuova autorizzazione esplicita dell'utente con tetto di tempo per catena. *(Coperta dall'obiettivo di sessione, che autorizza DB-07 e DB-08 senza fermarsi; nessun nuovo messaggio. Tetto del contratto: 60 min per richiesta, 60 × L per catena.)*
- [x] Tutte le celle con profilo; le ripetizioni extra della catena da 8 solo dove la regola di TBA-03 lo richiede.
- [x] Report finale con raccomandazione e limiti; nessun numero unico.

## Frontier
**Completato** (2026-09-27, skills-only). Il lotto `db07-pilot` è stato proseguito:
- catene da 3 su 45 celle;
- catena da 8 sulla ripetizione 1 (15 celle);
- ripetizione 2 della catena da 8 per `bare`, skills-only, Autopilot e c1a, come chiesto dalla
  regola di TBA-03, che è decisa a ogni lunghezza.

In tutto 270 richieste giudicate. Nessun guasto d'infrastruttura, timeout o riscontro
dell'audit; 119,10 $ stimati per DB-08. Report, raccomandazione e limiti:
[delivery-bench-results.md](../../../research/delivery-bench-results.md).

In sintesi:
- Su C e Python il braccio non conta.
- Sul frontend, skills-only è l'unico che non perde richieste (48/48 alla catena da 8 su tutti
  gli scenari, 0 regressioni). L'accettazione da sola non lo distingue da Pi nudo (Holm 0,094).
- Autopilot non è davanti su nessun asse, a 5,4× il costo.
- c3a in AFK si ferma sul cancello.

Correzioni nella stessa PR:
- lettura della bussola lungo la catena;
- difetto di una suite nascosta, corretto e rilegato con `amend-suite`; otto giudizi
  riclassificati esattamente e 30/30 alberi rigiudicati identici.

## Step-by-Step Implementation Plan
1. Autorizzazione.
2. Catene da 3, poi da 8.
3. Report finale.

## Testing Plan
Live.

## Out of Scope
- Migliorare i bracci nello stesso lotto.

```
