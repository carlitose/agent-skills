---
type: source
title: "QAO-01 — Show the evidence question the suite's end and its test folder"
identity_key: ticket:ticket-driver-qa-observation/QAO-01
identity_strength: stable
source_path: docs/tickets/ticket-driver-qa-observation/done/01-show-the-suite-end-and-test-folder.md
source_digest: sha256:94a6fba87ad454df8cc063c631a5fd577e7192493209e2cd06f3669ac2b39683
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-29
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# QAO-01 — Show the evidence question the suite's end and its test folder

Compiled from `docs/tickets/ticket-driver-qa-observation/done/01-show-the-suite-end-and-test-folder.md`. Identity is `ticket:ticket-driver-qa-observation/QAO-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-29** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-ticket-driver-qa-observation]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-driver-qa-observation-qao-01.md","payload_bytes":1706,"payload_sha256":"94a6fba87ad454df8cc063c631a5fd577e7192493209e2cd06f3669ac2b39683"}],"payload_bytes":1706,"payload_sha256":"94a6fba87ad454df8cc063c631a5fd577e7192493209e2cd06f3669ac2b39683","schema":1,"source_digest":"sha256:94a6fba87ad454df8cc063c631a5fd577e7192493209e2cd06f3669ac2b39683","source_identity":"ticket:ticket-driver-qa-observation/QAO-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1706,"payload_sha256":"94a6fba87ad454df8cc063c631a5fd577e7192493209e2cd06f3669ac2b39683","schema":1,"source_digest":"sha256:94a6fba87ad454df8cc063c631a5fd577e7192493209e2cd06f3669ac2b39683","source_identity":"ticket:ticket-driver-qa-observation/QAO-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "QAO-01"
execution_mode: AFK
blocked_by: []
---

# QAO-01 — Show the evidence question the suite's end and its test folder

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-qa-observation-01`
- Role: `ticket`
- Parent: [ticket-driver-qa-observation.md](../../specs/ticket-driver-qa-observation.md)

## Parent Spec
[ticket-driver-qa-observation.md](../../specs/ticket-driver-qa-observation.md)

## What to Build
Build the `qa.evidence_class` state from the end of stdout and the end of stderr, 4096 characters
each, instead of the head of `stdout + stderr`. Count a `testes/` folder as a test folder in
`TEST_PATH`.

## Acceptance Criteria
- [x] A verbose suite's verdict at the end of stdout, and the end of stderr, reach the state.
- [x] `testes/all.lua` is a test source.
- [x] Question, classes, thresholds, gate policy, source order and budget do not change.
- [x] All ticket-driver tests pass.

## Outcome
2026-09-29. RED: `test_the_evidence_question_sees_the_verdict_of_a_verbose_suite` and
`test_a_testes_folder_holds_tests` failed on the baseline. The state held only build notices,
and the Lua folder gave no sources. GREEN: both pass, and all ticket-driver tests pass.

## Frontier
Closed. The sql-engine gate and the gate policy for an undecidable class stay open, as the spec
says.

## Step-by-Step Implementation Plan
1. Rebuild the QA state of the three gated runs of lot `dbh` from their judge records.
2. Add the two RED tests.
3. Change `state.qa` and `TEST_PATH`.

## Testing Plan
Offline unit tests on the state and on a local Git repository; no Pi, model or network.

## Out of Scope
Source order and budget, gate policy, and past lot records.

```
