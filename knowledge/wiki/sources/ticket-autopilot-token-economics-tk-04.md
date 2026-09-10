---
type: source
title: "Compose the worst-case per-turn ceiling"
identity_key: ticket:autopilot-token-economics/TK-04
identity_strength: stable
source_path: docs/tickets/autopilot-token-economics/done/04-compose-worst-case-ceiling.md
source_digest: sha256:d8614312b160cceba443dc8e9ce7dfdf5d78e8fdfd4405d6ac5246634acd73e9
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-11
created_provenance: git-commit
disposition_changed: 2026-08-11
disposition_changed_provenance: git-rename
run_id: fdad98a7f91c4555
---

# Compose the worst-case per-turn ceiling

Compiled from `docs/tickets/autopilot-token-economics/done/04-compose-worst-case-ceiling.md`. Identity is `ticket:autopilot-token-economics/TK-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-11** via `git-commit`
- Disposition changed: **2026-08-11** via `git-rename`

## Graph

- Parent source: [[sources/artifact-autopilot-token-economics-wayfinder]]
- Blocked by: [[sources/ticket-autopilot-token-economics-tk-02]] — `ticket:autopilot-token-economics/TK-02`
- Blocked by: [[sources/ticket-autopilot-token-economics-tk-03]] — `ticket:autopilot-token-economics/TK-03`

## Run

Completed under autopilot run `fdad98a7f91c4555`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-token-economics-tk-04.md","payload_bytes":1912,"payload_sha256":"d8614312b160cceba443dc8e9ce7dfdf5d78e8fdfd4405d6ac5246634acd73e9"}],"payload_bytes":1912,"payload_sha256":"d8614312b160cceba443dc8e9ce7dfdf5d78e8fdfd4405d6ac5246634acd73e9","schema":1,"source_digest":"sha256:d8614312b160cceba443dc8e9ce7dfdf5d78e8fdfd4405d6ac5246634acd73e9","source_identity":"ticket:autopilot-token-economics/TK-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1912,"payload_sha256":"d8614312b160cceba443dc8e9ce7dfdf5d78e8fdfd4405d6ac5246634acd73e9","schema":1,"source_digest":"sha256:d8614312b160cceba443dc8e9ce7dfdf5d78e8fdfd4405d6ac5246634acd73e9","source_identity":"ticket:autopilot-token-economics/TK-04"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TK-04"
execution_mode: AFK
blocked_by:
  - "TK-02"
  - "TK-03"
---

# Compose the worst-case per-turn ceiling

## Artifact Graph

- Artifact ID: `artifact:tk-04-compose-worst-case-ceiling`
- Role: `ticket`
- Parent: [Autopilot Token Economics](../../specs/autopilot-token-economics-wayfinder.md)

## Type
Task

## What to Build
Compose the measured static prefix from `TK-02` with the declared intake bounds from `TK-03`
into a single worst-case per-turn context ceiling, and guard it against regression.

Neither input alone yields a per-turn number: the static prefix ignores volatile content, and
a declared bound is a contract rather than a measurement. Their composition is the strongest
statement this repository can prove without host telemetry.

## Acceptance Criteria
- [ ] The ceiling is computed from both inputs and reported in the frozen unit.
- [ ] The report names every assumption that makes it a worst case rather than an estimate.
- [ ] A regression check fails when the ceiling grows without a deliberate raise.
- [ ] Raising the ceiling is an explicit, reviewable action distinct from breaching it.
- [ ] The check adds no token axis to ledger budgets, gates, or merge authorization.
- [ ] Output states that the ceiling is an upper bound and not observed consumption.

## Frontier
Blocked by `TK-02` and `TK-03`.

## Step-by-Step Plan
1. Define the composition rule and its worst-case assumptions.
2. Extend the measurement output with the composed ceiling.
3. Add the regression check and the deliberate-raise procedure.
4. Document how a legitimate contract growth is distinguished from accidental bloat.

## Testing Plan
Fixtures for a stable ceiling, an accidental breach, and a deliberate raise. Assert the check
cannot gate a run, a delivery, or a merge.

## Out of Scope
- Live measurement.
- Making the ceiling a scheduling or delivery precondition.

```
