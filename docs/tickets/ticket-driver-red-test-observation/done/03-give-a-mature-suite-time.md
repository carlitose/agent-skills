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
