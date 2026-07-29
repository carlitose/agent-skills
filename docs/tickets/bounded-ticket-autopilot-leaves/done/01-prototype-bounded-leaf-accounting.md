---
ticket_schema: 1
ticket_id: "01"
execution_mode: AFK
blocked_by: []
---

# Prototype bounded leaf accounting and resumable handoffs

## Parent Spec

[bounded-ticket-autopilot-leaf-protocol.md](../../../specs/bounded-ticket-autopilot-leaf-protocol.md)

## What to Build

Build a disposable deterministic prototype for the budget, reservation, progress, partial
handoff, and ledger-version decisions required by
[GitHub issue #9](https://github.com/carlitose/agent-skills/issues/9). Model the real
two-ticket shape without modifying production scheduler behavior.

## Acceptance Criteria

- [ ] The model tracks quality failures, total leaf interactions, optional tool calls, and
      optional wall time as separate dimensions.
- [ ] Mandatory QA execution and verification reservations cannot be consumed by earlier
      review retries, and impossible configurations fail before a run starts.
- [ ] A leaf can stop with a versioned partial handoff containing exact CandidateRef,
      expected/inspected scope, commands, findings, remaining work, phase, and stop reason.
- [ ] Replaying a compatible partial handoff resumes only the remaining scope and does not
      repeat completed modeled work.
- [ ] Progress events are monotonic and idempotent; repeated status reads do not create
      duplicate progress.
- [ ] A changed CandidateRef invalidates every modeled semantic handoff and artifact.
- [ ] Fixtures reproduce a complete leaf, a timeout, an interruption/resume, budget
      exhaustion, reserved-stage protection, and stale-candidate rejection.
- [ ] The result recommends exact production schemas, budget arithmetic, and either an
      explicit ledger migration or a fail-closed version boundary.

## Frontier

Ready. This prototype resolves the contract and compatibility questions that block
production tickets `02` and `04`.

## Step-by-Step Implementation Plan

1. Capture the current ledger counters, stage transitions, CandidateRef invalidation, and
   delivery continuation as the known baseline.
2. Define small versioned prototype records for budgets, leaf context, progress, and partial
   handoff.
3. Implement pure transition/reduction functions and deterministic fixtures.
4. Exercise invalid configurations, interruption windows, stale references, and ledger
   replay.
5. Compare migration, version-bump, and fail-closed options for existing active runs.
6. Record the selected production contract and rejected alternatives in the parent spec or
   a linked decision record.

## Testing Plan

- Unit tests for arithmetic, reservations, transitions, replay, idempotency, and stale
  CandidateRef rejection.
- Scenario tests matching the interaction accounting and mandatory-stage pressure described
  in issue #9.
- Static comparison with current ledger and CLI contracts.
- No result from the prototype is runtime or live-provider evidence.

## Out of Scope

- Editing production scheduler, leaf skills, verification contracts, or delivery code.
- Choosing cross-CandidateRef evidence reuse.
- Live provider, database, browser, payment, credential, or human verification.
