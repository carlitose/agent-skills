---
ticket_schema: 1
ticket_id: "LB-01"
execution_mode: AFK
blocked_by: []
---

# Restore semantic-revalidation leaf capacity

## Artifact Graph

- Artifact ID: `artifact:lb-01-restore-semantic-revalidation-leaf-capacity`
- Role: `ticket`
- Parent: [reconciliation leaf-budget diagnostic](../../../specs/ticket-autopilot-reconciliation-leaf-budget-diagnostic.md)

## Parent Spec

[reconciliation leaf-budget diagnostic](../../../specs/ticket-autopilot-reconciliation-leaf-budget-diagnostic.md)

## What Was Built

Ticket Autopilot now gives every semantically new CandidateRef a fresh bounded leaf-budget
epoch, retains lifetime accounting in append-only history, repairs already-affected schema-4
runs through a public audited transition, and persists real exhaustion as an actionable gate.

## Acceptance Criteria

- [x] A regression starts from `pr-open` with seven of ten interactions consumed, reproduces
      the old verification deadlock after fresh review/QA, repairs it, and completes fresh
      verification and finalization.
- [x] Fresh CandidateRefs inherit no old pass, finding disposition, checkpoint, claim,
      reservation consumption, or merge authorization.
- [x] Status exposes current-epoch capacity while final verbosity retains lifetime
      interaction, tool-call, wall-time, invalidation, cache, and quality-failure metrics.
- [x] Same-CandidateRef retries remain bounded, optional work cannot consume mandatory slots,
      and real exhaustion opens a durable `resource-budget` gate.
- [x] Equivalent reconciliation preserves evidence and consumes no new leaf capacity.
- [x] Existing valid schema-4 ledgers resume through idempotent
      `revalidation-budget-repair` without manual edits.
- [x] Ledger replay validates the new append-only repair event and rejects unrelated mutation.
- [x] Focused leaf-protocol, kernel, semantic-reconciliation, CLI, and ledger tests pass.

## Implementation Notes

- `new_leaf_budget()` starts a new current-candidate epoch at semantic invalidation boundaries.
- `rebuild_leaf_budget_epoch()` deterministically reduces retained progress into current
  capacity.
- `Kernel.repair_revalidation_leaf_budget()` cross-checks retained progress against the
  append-only event suffix and refuses repairs that would erase retries.
- `Kernel.report()` derives lifetime resource totals from `leaf-result-recorded` history.
- The CLI exposes `revalidation-budget-repair` and converts true limit errors into a durable
  recovery gate.

## Testing

The regression covers the original 7/10 state, old 10/10 failure, audited repair, duplicate
repair, fresh verify/finalize, final lifetime/current projections, persistence, and reload.
CLI coverage proves a genuine three-interaction exhaustion returns success with a persisted
actionable gate instead of an uncaught transition error.

## Out of Scope

- Reusing evidence across changed CandidateRefs.
- Raising or removing same-candidate limits.
- Editing affected ledgers by hand.
- Changing wiki behavior, provider policy, or exact-head merge authorization.
