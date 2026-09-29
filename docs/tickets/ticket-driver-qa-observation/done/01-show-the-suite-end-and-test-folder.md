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
