---
type: source
title: "DB-01 — Contratto dell'oracolo e protocollo di esecuzione"
identity_key: ticket:delivery-bench/DB-01
identity_strength: stable
source_path: docs/tickets/delivery-bench/done/01-oracle-contract-and-run-protocol.md
source_digest: sha256:7c25432c99d3f87b5e4d4ee89239577c62fbc7a52041243e351933d66d2645ad
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-26
created_provenance: git-commit
disposition_changed: 2026-09-26
disposition_changed_provenance: git-rename
---

# DB-01 — Contratto dell'oracolo e protocollo di esecuzione

Compiled from `docs/tickets/delivery-bench/done/01-oracle-contract-and-run-protocol.md`. Identity is `ticket:delivery-bench/DB-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-26** via `git-commit`
- Disposition changed: **2026-09-26** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-bench]]
- Child source: [[sources/artifact-delivery-bench-oracle-contract]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[5],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[4],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-db-01.md","payload_bytes":3010,"payload_sha256":"7c25432c99d3f87b5e4d4ee89239577c62fbc7a52041243e351933d66d2645ad"}],"payload_bytes":3010,"payload_sha256":"7c25432c99d3f87b5e4d4ee89239577c62fbc7a52041243e351933d66d2645ad","schema":1,"source_digest":"sha256:7c25432c99d3f87b5e4d4ee89239577c62fbc7a52041243e351933d66d2645ad","source_identity":"ticket:delivery-bench/DB-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 4: What to Build |
| acceptance | 5: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3010,"payload_sha256":"7c25432c99d3f87b5e4d4ee89239577c62fbc7a52041243e351933d66d2645ad","schema":1,"source_digest":"sha256:7c25432c99d3f87b5e4d4ee89239577c62fbc7a52041243e351933d66d2645ad","source_identity":"ticket:delivery-bench/DB-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DB-01"
execution_mode: AFK
blocked_by: []
---

# DB-01 — Contratto dell'oracolo e protocollo di esecuzione

## Artifact Graph
- Artifact ID: `ticket:delivery-bench:01`
- Role: `ticket`
- Parent: [delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

### Produces
- [delivery-bench-oracle-contract.md](../../research/delivery-bench-oracle-contract.md)

## Parent Spec
[delivery-bench-wayfinder.md](../../specs/delivery-bench-wayfinder.md)

## What to Build
Definire in `docs/research/delivery-bench-oracle-contract.md` il contratto del benchmark: formato di una richiesta grezza, di uno scenario (stato iniziale pubblico, richieste 1..8, suite nascosta per richiesta, latenti, trappole con distanza), come la suite gira in un container contro un repo consegnato senza toccarlo, come ogni braccio riceve la richiesta N solo dopo la consegna della N-1, e il record del profilo a cinque assi. Chiarire come Autopilot riceve la richiesta grezza (spec e ticket li scrive il braccio; merge nel repo del benchmark, provider locale o repo effimero) e un tetto di tempo per catena. Riusare `bench38_harness.py` e `arm_comparison.py` dove possibile. Sezioni della mappa: Decisions 2-4, 6-7, 9-11, Not Yet Specified.

## Acceptance Criteria
- [x] Il documento risponde a ogni voce di *Not Yet Specified* della mappa o dichiara la domanda ancora aperta con il prossimo passo.
- [x] Un runner minimo esegue una suite nascosta d'esempio su un repo consegnato in un container e scrive un profilo JSON; il repo consegnato risulta byte-identico dopo l'esecuzione.
- [x] Le regole di isolamento sono verificabili: elenco esplicito di cosa il braccio vede a ogni richiesta e prova che la suite nascosta non è nel suo checkout.
- [x] Il protocollo di Autopilot è descritto passo per passo e provato una volta su un repo effimero senza chiamate al modello.

## Frontier
**Completato** in esecuzione skills-only (2026-09-26): contratto in `docs/research/delivery-bench-oracle-contract.md`; `benchmarks/delivery-bench/judge.py` con scenario d'esempio: 12 test offline, prova live in `python:3.12-slim` (riferimento 5/5, stub fallisce esattamente i 5 controlli attesi, albero consegnato identico); sonda Autopilot senza modello su repo effimero fino a `verified` e push del ramo di consegna (limiti nel contratto, §7). Merge registrato nella PR di consegna; spostato in `done/` senza ricevuta del runner.

## Step-by-Step Implementation Plan
1. Leggere bench38 (`/c/bench38`, `bench38_harness.py`, `acceptance.py`) e il runner Harbor usato per Terminal-Bench; decidere cosa si riusa.
2. Scrivere il contratto; provare il runner minimo su un repo giocattolo.
3. Provare il giro Autopilot senza modello su un repo effimero; registrare limiti.

## Testing Plan
Prova del runner minimo (repo consegnato immutato, profilo scritto); prova Autopilot senza modello. Nessun lotto live.

## Out of Scope
- Scrivere gli scenari (DB-03/04/05).
- Scegliere il vincitore o modificare i bracci.

```
