---
type: source
title: "DBH-29 — Copertura dei test limitata alla diff"
identity_key: ticket:delivery-bench-hard/DBH-29
identity_strength: stable
source_path: docs/tickets/delivery-bench-hard/done/29-diff-coverage.md
source_digest: sha256:ade2395d9ed591014084d6a977fd571d77c2256955b789338fc8a342bce0e784
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-06
created_provenance: git-commit
disposition_changed: 2026-10-06
disposition_changed_provenance: git-rename
---

# DBH-29 — Copertura dei test limitata alla diff

Compiled from `docs/tickets/delivery-bench-hard/done/29-diff-coverage.md`. Identity is `ticket:delivery-bench-hard/DBH-29`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-06** via `git-commit`
- Disposition changed: **2026-10-06** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-bench-hard-quality-judge]]
- Blocked by: [[sources/ticket-delivery-bench-hard-dbh-28]] — `ticket:delivery-bench-hard/DBH-28`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-bench-hard-dbh-29.md","payload_bytes":2556,"payload_sha256":"ade2395d9ed591014084d6a977fd571d77c2256955b789338fc8a342bce0e784"}],"payload_bytes":2556,"payload_sha256":"ade2395d9ed591014084d6a977fd571d77c2256955b789338fc8a342bce0e784","schema":1,"source_digest":"sha256:ade2395d9ed591014084d6a977fd571d77c2256955b789338fc8a342bce0e784","source_identity":"ticket:delivery-bench-hard/DBH-29","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 9: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 10: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2556,"payload_sha256":"ade2395d9ed591014084d6a977fd571d77c2256955b789338fc8a342bce0e784","schema":1,"source_digest":"sha256:ade2395d9ed591014084d6a977fd571d77c2256955b789338fc8a342bce0e784","source_identity":"ticket:delivery-bench-hard/DBH-29"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DBH-29"
execution_mode: AFK
blocked_by:
  - "DBH-28"
---

# DBH-29 — Copertura dei test limitata alla diff

## Artifact Graph
- Artifact ID: `ticket:delivery-bench-hard:29`
- Role: `ticket`
- Parent: [delivery-bench-hard-quality-judge.md](../../specs/delivery-bench-hard-quality-judge.md)

## Parent Spec
[delivery-bench-hard-quality-judge.md](../../specs/delivery-bench-hard-quality-judge.md)

## What to Build
`quality.py coverage` esegue il `test_command` dell'albero di ogni unità nell'immagine dello scenario, offline. Misura quante righe eseguibili aggiunte nei sorgenti, esclusi i test, vengono eseguite.

Per linguaggio:
- Python: `coverage.py`, in un'immagine derivata con versione fissata;
- C: build con `--coverage` e `gcov`;
- JavaScript: `NODE_V8_COVERAGE`. La mappatura da `dist/` a `src/` va verificata; se non è possibile, si usa un fallback esplicito e lo si riporta.

Spec: Target behavior 3.

## Acceptance Criteria
- [x] Per ogni unità c'è una quota con righe aggiunte, eseguibili e coperte, oppure "n/a" con il motivo.
- [x] L'immagine derivata per Python si costruisce da un Dockerfile versionato in `quality_coverage.py`
      (`FROM` l'immagine dello scenario, `coverage==7.16.2`). Scelta fatta durante l'implementazione: il
      Dockerfile sta nel codice che lo usa, non in `dbench-private`.
- [x] Smoke su un'unità reale per scenario.

## Evidence
- Merged in #436 (code) and #438 (Python: worker processes traced, generated code skipped).
- Real smoke, dbh-luna3d pi-tools r1 request 2: crdt-yjs 12/12, lua-vm 49/51, sql-engine 59/63
  added executable lines covered (sql-engine 688 s with `COVERAGE_CORE=sysmon`).

## Frontier
Bloccato da DBH-28. L'esecuzione sui lotti veri aspetta la fine di `dbh-luna3e`.

## Gates
Come la spec:
- un tentativo è un giudizio completo di `dbh-luna3d` più `dbh-luna3e`;
- nessun tetto di budget né di tempo, con la spesa riportata;
- al massimo 2 tentativi, il pilota e il giudizio completo;
- nessuna versione esatta;
- merge con CI 8/8 e `--match-head-commit`.

Blocco: niente esecuzioni Docker o Opus sui lotti veri finché `dbh-luna3e` gira.

## Step-by-Step Implementation Plan
1. Calcolare le righe aggiunte dalla diff, nei file sorgente e non nei test.
2. Scrivere un adattatore per ogni linguaggio.
3. Eseguire in Docker con il timeout dello scenario.

## Testing Plan
- Test unitari delle righe aggiunte e del calcolo della quota, su output di coverage finti.
- Smoke Docker su un'unità per scenario.

## Out of Scope
- Mutation (DBH-30).

```
