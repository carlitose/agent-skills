---
type: source
title: "RTO-03 — Give a mature suite time to finish"
identity_key: ticket:ticket-driver-red-test-observation/RTO-03
identity_strength: stable
source_path: docs/tickets/ticket-driver-red-test-observation/done/03-give-a-mature-suite-time.md
source_digest: sha256:02f97e85a0f645dc36887b536c5abd9bef48066b027786da2998811384624a73
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-29
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# RTO-03 — Give a mature suite time to finish

Compiled from `docs/tickets/ticket-driver-red-test-observation/done/03-give-a-mature-suite-time.md`. Identity is `ticket:ticket-driver-red-test-observation/RTO-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-29** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-ticket-driver-red-test-observation]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-driver-red-test-observation-rto-03.md","payload_bytes":1631,"payload_sha256":"02f97e85a0f645dc36887b536c5abd9bef48066b027786da2998811384624a73"}],"payload_bytes":1631,"payload_sha256":"02f97e85a0f645dc36887b536c5abd9bef48066b027786da2998811384624a73","schema":1,"source_digest":"sha256:02f97e85a0f645dc36887b536c5abd9bef48066b027786da2998811384624a73","source_identity":"ticket:ticket-driver-red-test-observation/RTO-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1631,"payload_sha256":"02f97e85a0f645dc36887b536c5abd9bef48066b027786da2998811384624a73","schema":1,"source_digest":"sha256:02f97e85a0f645dc36887b536c5abd9bef48066b027786da2998811384624a73","source_identity":"ticket:ticket-driver-red-test-observation/RTO-03"} -->
```markdown
---
ticket_schema: 1
ticket_id: "RTO-03"
execution_mode: AFK
blocked_by: []
---

# RTO-03 — Give a mature suite time to finish

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-red-test-observation-03`
- Role: `ticket`
- Parent: [ticket-driver-red-test-observation.md](../../specs/ticket-driver-red-test-observation.md)

## Parent Spec
[ticket-driver-red-test-observation.md](../../specs/ticket-driver-red-test-observation.md)

## What to Build
Raise the shipped `test_timeout_seconds` of `ticket-driver/policy.json` from 180 to 600, so the
driver no longer kills a mature project suite that is still running and counts it as red tests.

## Acceptance Criteria
- [x] The shipped test timeout is at least four times the slowest sql-engine suite run of lot
  `dbh` (136 s).
- [x] All ticket-driver tests pass.

## Outcome
2026-09-29. RED: `test_the_shipped_policy_gives_a_mature_suite_time_to_finish` failed on the
baseline (180 < 544). GREEN: it passes with 600, and all ticket-driver tests pass.

In lot `dbh` the sql-engine suite ran 71 to 136 s in the driver. In lot `dbh-drivers`, with four
sql-engine cells running at once, 9 of 11 runs passed 180 s and were killed.

## Frontier
Closed. The next driver measurement binds the new policy hash.

## Step-by-Step Implementation Plan
1. Collect the test durations of the sql-engine driver runs of lots `dbh` and `dbh-drivers`.
2. Add the RED policy test, then raise the shipped timeout.

## Testing Plan
Offline test of the shipped policy; no Pi, model or network.

## Out of Scope
The leaf timeout, the order in which the benchmark runs its cells, and past lot records.

```
