---
type: source
title: "Write the token-reduction guide"
identity_key: ticket:autopilot-token-economics/TK-06
identity_strength: stable
source_path: docs/tickets/autopilot-token-economics/done/06-write-token-reduction-guide.md
source_digest: sha256:72376a16aab1eb34849c48937b9a65a8c5c68ab2dad399e6c4c6aefa3ab6d404
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-11
created_provenance: git-commit
disposition_changed: 2026-08-11
disposition_changed_provenance: git-rename
run_id: fdad98a7f91c4555
---

# Write the token-reduction guide

Compiled from `docs/tickets/autopilot-token-economics/done/06-write-token-reduction-guide.md`. Identity is `ticket:autopilot-token-economics/TK-06`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-11** via `git-commit`
- Disposition changed: **2026-08-11** via `git-rename`

## Graph

- Parent source: [[sources/artifact-autopilot-token-economics-wayfinder]]
- Blocked by: [[sources/ticket-autopilot-token-economics-tk-02]] — `ticket:autopilot-token-economics/TK-02`

## Run

Completed under autopilot run `fdad98a7f91c4555`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-token-economics-tk-06.md","payload_bytes":2007,"payload_sha256":"72376a16aab1eb34849c48937b9a65a8c5c68ab2dad399e6c4c6aefa3ab6d404"}],"payload_bytes":2007,"payload_sha256":"72376a16aab1eb34849c48937b9a65a8c5c68ab2dad399e6c4c6aefa3ab6d404","schema":1,"source_digest":"sha256:72376a16aab1eb34849c48937b9a65a8c5c68ab2dad399e6c4c6aefa3ab6d404","source_identity":"ticket:autopilot-token-economics/TK-06","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2007,"payload_sha256":"72376a16aab1eb34849c48937b9a65a8c5c68ab2dad399e6c4c6aefa3ab6d404","schema":1,"source_digest":"sha256:72376a16aab1eb34849c48937b9a65a8c5c68ab2dad399e6c4c6aefa3ab6d404","source_identity":"ticket:autopilot-token-economics/TK-06"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TK-06"
execution_mode: AFK
blocked_by:
  - "TK-02"
---

# Write the token-reduction guide

## Artifact Graph

- Artifact ID: `artifact:tk-06-write-token-reduction-guide`
- Role: `ticket`
- Parent: [Autopilot Token Economics](../../specs/autopilot-token-economics-wayfinder.md)

## Type
Task

## What to Build
Operator guidance for running autopilot at lower context cost, quoting measured numbers from
`TK-02` rather than plausible ones.

Cover the practices named in the issue and explain why each works or does not:

- Context reset, and when a fresh session is cheaper than continuing an accumulated one.
- Small-context delegation, including that inline composition is the portable default and
  delegation requires explicit authority.
- Cache-friendly practice: a stable static prefix is reused across turns, so churning it for
  small edits is counterproductive, while injecting large volatile content early is
  expensive.

## Acceptance Criteria
- [ ] Every quantitative statement traces to `TK-02` output or is marked as unmeasured.
- [ ] The guide states which practices are operator behaviour and which are contract
      behaviour.
- [ ] It does not claim a percentage saving, a cost saving, or a cache hit rate that no local
      evidence observed.
- [ ] It records that live per-run totals require the `TK-09` observation.
- [ ] Guidance never suggests weakening verification to save context.

## Frontier
Blocked by `TK-02`. Publishing before measurement would produce plausible but unverified
numbers.

## Step-by-Step Plan
1. Generate current figures from the measurement command.
2. Write each practice with its mechanism and its evidence status.
3. Mark every unmeasured claim explicitly and link the live gate.

## Testing Plan
A documentation check that quoted figures match generated output, so the guide fails rather
than drifts when numbers change.

## Out of Scope
- Measuring live consumption.
- Recommending prose compression as a primary lever.

```
