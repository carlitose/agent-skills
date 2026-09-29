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
