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
