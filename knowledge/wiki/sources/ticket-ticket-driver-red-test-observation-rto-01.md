---
type: source
title: "RTO-01 — Show the retry question the end of each stream"
identity_key: ticket:ticket-driver-red-test-observation/RTO-01
identity_strength: stable
source_path: docs/tickets/ticket-driver-red-test-observation/done/01-show-the-end-of-each-stream.md
source_digest: sha256:57b254a7bdb49be021dcc4c8bb16f6e4da7de7d45d94de0d5dee23b12c84abed
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-29
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# RTO-01 — Show the retry question the end of each stream

Compiled from `docs/tickets/ticket-driver-red-test-observation/done/01-show-the-end-of-each-stream.md`. Identity is `ticket:ticket-driver-red-test-observation/RTO-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-29** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-ticket-driver-red-test-observation]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-driver-red-test-observation-rto-01.md","payload_bytes":1834,"payload_sha256":"57b254a7bdb49be021dcc4c8bb16f6e4da7de7d45d94de0d5dee23b12c84abed"}],"payload_bytes":1834,"payload_sha256":"57b254a7bdb49be021dcc4c8bb16f6e4da7de7d45d94de0d5dee23b12c84abed","schema":1,"source_digest":"sha256:57b254a7bdb49be021dcc4c8bb16f6e4da7de7d45d94de0d5dee23b12c84abed","source_identity":"ticket:ticket-driver-red-test-observation/RTO-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1834,"payload_sha256":"57b254a7bdb49be021dcc4c8bb16f6e4da7de7d45d94de0d5dee23b12c84abed","schema":1,"source_digest":"sha256:57b254a7bdb49be021dcc4c8bb16f6e4da7de7d45d94de0d5dee23b12c84abed","source_identity":"ticket:ticket-driver-red-test-observation/RTO-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "RTO-01"
execution_mode: AFK
blocked_by: []
---

# RTO-01 — Show the retry question the end of each stream

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-red-test-observation-01`
- Role: `ticket`
- Parent: [ticket-driver-red-test-observation.md](../../specs/ticket-driver-red-test-observation.md)

## Parent Spec
[ticket-driver-red-test-observation.md](../../specs/ticket-driver-red-test-observation.md)

## What to Build
When the driver's test run is red, build the `retry.recoverable` state from the end of stdout and
the end of stderr separately, instead of from the head of `stderr + stdout`.

## Acceptance Criteria
- [x] With build noise on stderr and the verdict at the end of stdout, the retry question sees the
  verdict. On the baseline it saw only the noise.
- [x] With the verdict at the end of stderr behind long stdout, the retry question still sees it.
- [x] Question, thresholds, cascade and gate policy are unchanged; the observation stays bounded.

## Outcome
2026-09-29. The first new test in `test_c2.py` failed on the baseline: the state held only the
repeated build warning. With `state.red_tests` both tests pass, together with the other
ticket-driver tests (63).

## Frontier
Closed. It applies to the next driver run; past lots are unchanged.

## Step-by-Step Implementation Plan
1. RED test: red tests with stderr build noise and the verdict at the end of stdout.
2. `state.red_tests(stdout, stderr)` with a 4096-character tail per stream, used by `driver.py`.
3. Guard test with the verdict at the end of stderr; full ticket-driver tests.

## Testing Plan
Fake Pi leaf and loopback fake Jev, with a real test command that prints to both streams.

## Out of Scope
The `qa.evidence_class` and `review.*` gates, the c1b stop path, Jev policy, and past lot records.

```
