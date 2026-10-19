---
type: source
title: "TBA-07 — Lotti c1a e c3a sui 63 task originali"
identity_key: ticket:terminal-bench-best-arm/TBA-07
identity_strength: stable
source_path: docs/tickets/terminal-bench-best-arm/07-run-driver-lots.md
source_digest: sha256:89e7029dd1c817c88563adc76b7d220718d439eba4dbb8656f9523948f38db68
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-26
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# TBA-07 — Lotti c1a e c3a sui 63 task originali

Compiled from `docs/tickets/terminal-bench-best-arm/07-run-driver-lots.md`. Identity is `ticket:terminal-bench-best-arm/TBA-07`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-26** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-terminal-bench-best-arm]]
- Blocked by: [[sources/ticket-terminal-bench-best-arm-tba-06]] — `ticket:terminal-bench-best-arm/TBA-06`
- Blocked by: [[sources/ticket-terminal-bench-best-arm-tba-02]] — `ticket:terminal-bench-best-arm/TBA-02`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-terminal-bench-best-arm-tba-07.md","payload_bytes":1554,"payload_sha256":"89e7029dd1c817c88563adc76b7d220718d439eba4dbb8656f9523948f38db68"}],"payload_bytes":1554,"payload_sha256":"89e7029dd1c817c88563adc76b7d220718d439eba4dbb8656f9523948f38db68","schema":1,"source_digest":"sha256:89e7029dd1c817c88563adc76b7d220718d439eba4dbb8656f9523948f38db68","source_identity":"ticket:terminal-bench-best-arm/TBA-07","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1554,"payload_sha256":"89e7029dd1c817c88563adc76b7d220718d439eba4dbb8656f9523948f38db68","schema":1,"source_digest":"sha256:89e7029dd1c817c88563adc76b7d220718d439eba4dbb8656f9523948f38db68","source_identity":"ticket:terminal-bench-best-arm/TBA-07"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TBA-07"
execution_mode: AFK
blocked_by:
  - "TBA-06"
  - "TBA-02"
---

# TBA-07 — Lotti c1a e c3a sui 63 task originali

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-best-arm:07`
- Role: `ticket`
- Parent: [terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## Parent Spec
[terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## What to Build
Eseguire una ripetizione dei 63 task (GPU esclusi) per c1a e poi per c3a, con la stessa policy flat-rate, `-n 3` e `no_network_docker` di skills-only, in serie dopo TBA-02, e ripetere le celle fallite per infrastruttura. Sezione spec: Decisions 1–3, Generic ticket-driver arms.

## Acceptance Criteria
- [ ] Lot, authority e ledger propri per braccio, fuori da Git, vincolati alla head integrata di TBA-06.
- [ ] Ogni cella avviata al più una volta nel lotto principale; le celle `infra:*` ripetute in lotti separati, al massimo due volte; intenti originali intatti.
- [ ] Per ogni cella restano result.json di Harbor, ricevuta, journal modello e Jev, fasi eseguite, verdetto e correzione.

## Frontier
Bloccato da TBA-06 e dalla fine di TBA-02.

## Step-by-Step Implementation Plan
1. Attendere la chiusura di TBA-02 senza container attivi.
2. Lotto c1a, retry infra; lotto c3a, retry infra.
3. Riassunto grezzo per TBA-03.

## Testing Plan
Controlli live su ledger, journal e result.json; classificazione con `retry_classification.py`.

## Out of Scope
- Modifiche all'agente durante i lotti.
- Task GPU o ripetizioni extra.

```
