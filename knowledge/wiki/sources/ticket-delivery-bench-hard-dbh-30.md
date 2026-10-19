---
type: source
title: "DBH-30 — Forza dei test: mutation limitata alla diff"
identity_key: ticket:delivery-bench-hard/DBH-30
identity_strength: stable
source_path: docs/tickets/delivery-bench-hard/done/30-diff-mutation.md
source_digest: sha256:d8cf434137c86daec1d38619d4c461280e332313a213253d41d30854bf9ed6ad
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-06
created_provenance: git-commit
disposition_changed: 2026-10-06
disposition_changed_provenance: git-rename
---

# DBH-30 — Forza dei test: mutation limitata alla diff

Compiled from `docs/tickets/delivery-bench-hard/done/30-diff-mutation.md`. Identity is `ticket:delivery-bench-hard/DBH-30`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-06** via `git-commit`
- Disposition changed: **2026-10-06** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-bench-hard-quality-judge]]
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-29]] — `ticket:delivery-bench-hard/DBH-29`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-hard-dbh-30.md","payload_bytes":2219,"payload_sha256":"d8cf434137c86daec1d38619d4c461280e332313a213253d41d30854bf9ed6ad"}],"payload_bytes":2219,"payload_sha256":"d8cf434137c86daec1d38619d4c461280e332313a213253d41d30854bf9ed6ad","schema":1,"source_digest":"sha256:d8cf434137c86daec1d38619d4c461280e332313a213253d41d30854bf9ed6ad","source_identity":"ticket:delivery-bench-hard/DBH-30","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 9: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 10: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2219,"payload_sha256":"d8cf434137c86daec1d38619d4c461280e332313a213253d41d30854bf9ed6ad","schema":1,"source_digest":"sha256:d8cf434137c86daec1d38619d4c461280e332313a213253d41d30854bf9ed6ad","source_identity":"ticket:delivery-bench-hard/DBH-30"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DBH-30"
execution_mode: AFK
blocked_by:
  - "DBH-29"
---

# DBH-30 — Forza dei test: mutation limitata alla diff

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:30`
- Role: `ticket`
- Parent: [delivery-bench-hard-quality-judge.md](../../specs/delivery-bench-hard-quality-judge.md)

## Parent Spec
[delivery-bench-hard-quality-judge.md](../../specs/delivery-bench-hard-quality-judge.md)

## What to Build
`quality.py mutation` genera mutanti deterministici, con seme fisso e al massimo N per unità, solo sulle righe aggiunte nei sorgenti. Esegue il `test_command` su ciascun mutante e lo classifica come ucciso, sopravvissuto, timeout o non compilabile; i non compilabili sono esclusi dalla quota. Riusa l'esecuzione Docker di DBH-29.

Spec: Target behavior 4.

## Acceptance Criteria
- [x] Lo stesso seme produce gli stessi mutanti.
- [x] Per ogni unità c'è la quota uccisi/(uccisi+sopravvissuti+timeout), con l'elenco dei sopravvissuti.
- [x] Smoke su un'unità reale per scenario.

## Evidence
- Seed 30, at most 8 mutants per unit; mutants on lines the tests never run survive unrun.
- Real smoke, dbh-luna3d pi-tools r1 request 2: crdt-yjs 6/8 killed (failing baseline,
  compared by failed test names), lua-vm 5 killed 2 survived 1 timeout, sql-engine 6/8.
- Choice made during implementation: a C unit whose own suite fails is `n/a`, because
  `all.lua` stops at the first failure and names no test.

## Frontier
Bloccato da DBH-29.

## Gates
Come la spec:
- un tentativo è un giudizio completo di `dbh-luna3d` più `dbh-luna3e`;
- nessun tetto di budget né di tempo, con la spesa riportata;
- al massimo 2 tentativi, il pilota e il giudizio completo;
- nessuna versione esatta;
- merge con CI 8/8 e `--match-head-commit`.

Blocco: niente esecuzioni Docker o Opus sui lotti veri finché `dbh-luna3e` gira.

## Step-by-Step Implementation Plan
1. Scrivere gli operatori per C, Python e JavaScript, applicati al testo della riga.
2. Applicare ogni mutante a una copia dell'albero.
3. Eseguire con timeout e misurare il tempo.

## Testing Plan
- Test unitari del generatore e del conteggio.
- Smoke Docker.

## Out of Scope
- Mutanti fuori dalle righe aggiunte.

```
