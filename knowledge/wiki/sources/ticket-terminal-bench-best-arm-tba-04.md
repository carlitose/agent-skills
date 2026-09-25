---
type: source
title: "TBA-04 — Sviluppare il braccio vincitore senza adattarsi al benchmark"
identity_key: ticket:terminal-bench-best-arm/TBA-04
identity_strength: stable
source_path: docs/tickets/terminal-bench-best-arm/04-develop-the-winner.md
source_digest: sha256:ba5557b44728087ecd43a051f3cb5ecf7b8e9b727bdfd4a49108296158126af6
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-25
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# TBA-04 — Sviluppare il braccio vincitore senza adattarsi al benchmark

Compiled from `docs/tickets/terminal-bench-best-arm/04-develop-the-winner.md`. Identity is `ticket:terminal-bench-best-arm/TBA-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-25** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-terminal-bench-best-arm]]
- Blocked by: [[sources/ticket-terminal-bench-best-arm-tba-03]] — `ticket:terminal-bench-best-arm/TBA-03`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-terminal-bench-best-arm-tba-04.md","payload_bytes":1568,"payload_sha256":"ba5557b44728087ecd43a051f3cb5ecf7b8e9b727bdfd4a49108296158126af6"}],"payload_bytes":1568,"payload_sha256":"ba5557b44728087ecd43a051f3cb5ecf7b8e9b727bdfd4a49108296158126af6","schema":1,"source_digest":"sha256:ba5557b44728087ecd43a051f3cb5ecf7b8e9b727bdfd4a49108296158126af6","source_identity":"ticket:terminal-bench-best-arm/TBA-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1568,"payload_sha256":"ba5557b44728087ecd43a051f3cb5ecf7b8e9b727bdfd4a49108296158126af6","schema":1,"source_digest":"sha256:ba5557b44728087ecd43a051f3cb5ecf7b8e9b727bdfd4a49108296158126af6","source_identity":"ticket:terminal-bench-best-arm/TBA-04"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TBA-04"
execution_mode: AFK
blocked_by:
  - "TBA-03"
---

# TBA-04 — Sviluppare il braccio vincitore senza adattarsi al benchmark

## Artifact Graph
- Artifact ID: `ticket:terminal-bench-best-arm:04`
- Role: `ticket`
- Parent: [terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## Parent Spec
[terminal-bench-best-arm.md](../../specs/terminal-bench-best-arm.md)

## What to Build
Migliorare il vincitore usando solo traiettorie e verifier dei task dev: tassonomia dei fallimenti, piccole modifiche mirate (system prompt, contenuto delle skill, ergonomia del tool sandbox, abitudini di verifica e stop), rilancio dev, poi una misura held-out e una completa. Sezioni spec: Decision 4, Invariants.

## Acceptance Criteria
- [ ] Ogni modifica è motivata da fallimenti dev citati; nessun log del verifier held-out è letto prima della misura finale.
- [ ] Una modifica è accettata solo se migliora dev e non peggiora held-out rispetto al vincitore di TBA-03.
- [ ] Il report finale separa i risultati dev, held-out e 63-task e cita ogni lotto; ci si ferma dopo tre iterazioni dev senza guadagno superiore a 2 task.

## Frontier
Bloccato da TBA-03.

## Step-by-Step Implementation Plan
1. Tassonomia dei fallimenti dev dalle traiettorie.
2. Iterazioni: modifica, test offline, lotto dev.
3. Misura held-out e completa; report; PR e merge.

## Testing Plan
Test offline per ogni modifica dell'adapter; lotti live dev/held-out con ledger propri.

## Out of Scope
- Nuovi modelli, task GPU, pubblicazione su leaderboard.

```
