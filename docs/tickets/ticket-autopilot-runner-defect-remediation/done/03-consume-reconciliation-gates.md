---
ticket_schema: 1
ticket_id: "RDR-03"
execution_mode: AFK
blocked_by: []
---

# Consume all resolved reconciliation gates

## Artifact Graph

- Artifact ID: `artifact:rdr-03-consume-reconciliation-gates`
- Role: `ticket`
- Parent: [Ticket Autopilot Runner Defect Remediation](../../specs/ticket-autopilot-runner-defect-remediation.md)

## Parent Spec

[Ticket Autopilot Runner Defect Remediation](../../specs/ticket-autopilot-runner-defect-remediation.md)

## What to Build

Fix GitHub issue [#202](https://github.com/carlitose/agent-skills/issues/202). A successful Git-derived reconciliation must consume every open gate on that ticket that represents the resolved reconciliation condition—`provider-merge`, `stack-reconciliation`, and `stack-reconciliation-recovery`—while preserving unrelated gates.

## Acceptance Criteria

- [ ] A focused regression fails on the current baseline by completing ordinary reconciliation with both provider-merge and stack-reconciliation gates open and observing a residual open stack gate.
- [ ] One canonical selector defines the exact reconciliation-condition gate categories and is reused by ordinary, proposal-backed, and recovery paths.
- [ ] The exact selected gate IDs are passed and consumed with explicit scheduler/proposal evidence in the same persisted reconciliation transition; a failed preparation cannot leave a partial durable closure.
- [ ] Successful equivalent and revalidation-required preparation close the resolved old-head condition before advancing; exact replay returns the same closed set.
- [ ] Human/start, source, provider-environment, resource-budget, verification, publication, wiki, Pi, and unrelated ticket/run gates remain unchanged.
- [ ] Ledger history records which gate IDs were consumed and validates replay literally.
- [ ] Reconciliation, proposal recovery, gate, ledger, autonomous merge, and terminal-boundary regressions pass.

## Frontier

Ready. The current `_merge_gate_ids()` selects only `provider-merge`; other reconciliation paths maintain separate category lists.

## Step-by-Step Implementation Plan

1. Add ordinary and proposal-backed failing fixtures with mixed relevant/unrelated gate sets.
2. Centralize reconciliation-condition gate selection without broad category matching.
3. Bind gate consumption to the successful reconciliation state transition and append exact IDs/evidence.
4. Prove rollback on preparation failure, idempotent replay, and unrelated-gate preservation.
5. Run focused/full kernel, ledger, CLI, reconciliation, and terminal suites plus compilation and graph checks.

## Testing Plan

Use kernel transaction fixtures and public resume integration with fake provider/Git state. Assert gate states, event order, consumed IDs, rollback, ticket state, merge readiness, and replay-derived run state.

## Out of Scope

- Auto-approving any human or authority gate.
- Closing provider/environment gates whose condition was not resolved by reconciliation.
- Rewriting historical gate events or reasons.
