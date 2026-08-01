---
ticket_schema: 1
ticket_id: "03"
execution_mode: AFK
blocked_by:
  - "02"
---

# Reconcile an external merge atomically

## Parent Spec

[ticket-autopilot-delivery-merge-wayfinder.md](../../specs/ticket-autopilot-delivery-merge-wayfinder.md)

## What to Build

Resolve the external-merge half of
[GitHub issue #17](https://github.com/carlitose/agent-skills/issues/17). Make
`approve --external-merge` perform live provider readback for the ledger-recorded PR,
verify that the exact recorded head is already merged, persist the human/external evidence,
and transition the ticket to `integrated` in the same locked, replay-safe operation.

This path observes and reconciles a merge; it never invokes a merge command. Repeating the
command after success must converge on the same integrated state and receipt without
requiring a second semantic authorization or `integrate` event.

## Evidence

- Current `_approve` chooses external mode only when the provider lacks the expected-head
  merge capability, then calls `Kernel.authorize_merge` without live PR readback.
- Current `integrate` separately calls `GET_PR_STATE`, records its receipt, and requires the
  prior authorization, creating the two-command recovery reported in the issue.
- `Kernel.record_integration` rejects an already provider-merged exact head until
  authorization has been stored, even though that same external action is the evidence
  being reconciled.
- The existing Azure external-merge test explicitly performs `approve --external-merge`
  and a later `integrate`; it is the direct regression fixture to replace and extend.

## Acceptance Criteria

- [ ] `approve --external-merge` performs live provider readback using only the PR ID stored
      in the ledger and validates provider identity, PR identity, merged state, and exact
      recorded head SHA.
- [ ] A matching observation records external authorization evidence and integration
      atomically under the run lock, returning `integrated` in that command.
- [ ] The external path never invokes a provider merge/complete operation.
- [ ] A provider head mismatch, wrong PR/provider, open/closed-unmerged state, simulated
      receipt, or missing evidence fails closed without partially authorizing or integrating.
- [ ] Repeating the exact reconciliation after integration is idempotent and returns the
      same terminal identity without appending contradictory effects or history.
- [ ] Crash recovery after provider readback but before ledger save converges on one
      external receipt and one integration transition.
- [ ] Run completion, dependent-ticket readiness, and status/report projections update in
      the same command; no later `integrate` event is required.
- [ ] GitHub and Azure DevOps fake-provider tests cover successful reconciliation,
      mismatches, provider failure, and replay.

## Frontier

Dependency-blocked by ticket `02`, which establishes the shared authorization and
merge-critical-path state/receipt contract that this external observation path reuses.

## Step-by-Step Implementation Plan

1. Define the external reconciliation command result and receipt identity as a distinct
   non-mutating provider path within the merge-critical ledger contract from ticket `02`.
2. Refactor `approve --external-merge` to require live provider mode, read the recorded PR,
   and validate provider/PR/head/merged state before any authorization or lifecycle write.
3. Add one kernel transaction that records external actor/evidence, the validated provider
   observation, and `integrated`, with an exact idempotent replay rule for already
   integrated tickets.
4. Remove the need for a follow-up caller `integrate` event on this path while keeping any
   internal compatibility behavior explicit and fail closed.
5. Update run-state/dependency projections and replace the two-step Azure regression test;
   add GitHub parity, mismatch, crash-window, and repeated-command tests.

## Testing Plan

Run ticket-autopilot CLI, kernel, ledger replay, provider, scheduling, and forward-test
suites. Stateful fake providers must prove that no merge command occurs, the exact stored
PR/head is read, partial writes do not survive failed validation, one successful command
completes the run or unblocks dependents, and a repeated command is a no-op projection of
the same integration.

## Out of Scope

- Performing a normal runner merge or weakening its explicit human authorization.
- Accepting a merge of a different head, another PR, or an unverified provider receipt.
- PR-body generation/publication or unrelated delivery effects.
- Live credentials, remote cleanup, or provider-specific orchestration in the core.

