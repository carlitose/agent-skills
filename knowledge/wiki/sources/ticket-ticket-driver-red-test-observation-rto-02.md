---
type: source
title: "RTO-02 — Keep a verbose passing suite alive"
identity_key: ticket:ticket-driver-red-test-observation/RTO-02
identity_strength: stable
source_path: docs/tickets/ticket-driver-red-test-observation/done/02-keep-a-verbose-suite-alive.md
source_digest: sha256:ede4ae3459bb0a8a861e6df2cd00a9bbadd80c70bedf7adf807d9fc6618b8b14
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-29
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# RTO-02 — Keep a verbose passing suite alive

Compiled from `docs/tickets/ticket-driver-red-test-observation/done/02-keep-a-verbose-suite-alive.md`. Identity is `ticket:ticket-driver-red-test-observation/RTO-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-29** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-ticket-driver-red-test-observation]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-driver-red-test-observation-rto-02.md","payload_bytes":1894,"payload_sha256":"ede4ae3459bb0a8a861e6df2cd00a9bbadd80c70bedf7adf807d9fc6618b8b14"}],"payload_bytes":1894,"payload_sha256":"ede4ae3459bb0a8a861e6df2cd00a9bbadd80c70bedf7adf807d9fc6618b8b14","schema":1,"source_digest":"sha256:ede4ae3459bb0a8a861e6df2cd00a9bbadd80c70bedf7adf807d9fc6618b8b14","source_identity":"ticket:ticket-driver-red-test-observation/RTO-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1894,"payload_sha256":"ede4ae3459bb0a8a861e6df2cd00a9bbadd80c70bedf7adf807d9fc6618b8b14","schema":1,"source_digest":"sha256:ede4ae3459bb0a8a861e6df2cd00a9bbadd80c70bedf7adf807d9fc6618b8b14","source_identity":"ticket:ticket-driver-red-test-observation/RTO-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "RTO-02"
execution_mode: AFK
blocked_by: []
---

# RTO-02 — Keep a verbose passing suite alive

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-red-test-observation-02`
- Role: `ticket`
- Parent: [ticket-driver-red-test-observation.md](../../specs/ticket-driver-red-test-observation.md)

## Parent Spec
[ticket-driver-red-test-observation.md](../../specs/ticket-driver-red-test-observation.md)

## What to Build
Raise the shipped `max_output_bytes` of `ticket-driver/policy.json` from 65536 to 8388608
(8 MiB), so the capture no longer kills a test suite that passes but prints more than 64 KiB.
The limit stays as a guard against runaway output.

## Acceptance Criteria
- [x] Under the shipped policy, a test run that prints 128 KiB and passes gets receipt
  `exit_code` 0 with no failure, and the run integrates.
- [x] The receipt keeps the full output of that run.
- [x] All ticket-driver tests pass.

## Outcome
2026-09-29. RED: `test_a_verbose_passing_suite_is_integrated_under_the_shipped_policy` failed
on the baseline. The receipt had `failure` `output-limit`, no exit code, and the run failed as
red tests. GREEN: it passes with the new limit, and all ticket-driver tests pass.

The crdt-yjs suite at its seed commit passes, and prints about 87 KB in about 30 seconds.

## Frontier
Closed. The next driver measurement binds the new policy hash.

## Step-by-Step Implementation Plan
1. Count the test receipts of lot `dbh` that ended with `output-limit`.
2. Run the crdt-yjs suite at its seed commit and measure its output.
3. Add the RED test with a verbose fake suite, then raise the shipped limit.

## Testing Plan
Offline test with the fake leaf and a local Git repository; no Pi, model or network.

## Out of Scope
Changing the capture itself (head and tail instead of a kill), the `qa` state's head of the
receipt, and past lot records.

```
