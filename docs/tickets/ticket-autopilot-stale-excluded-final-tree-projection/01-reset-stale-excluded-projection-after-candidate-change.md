---
ticket_schema: 1
ticket_id: "FPR-01"
execution_mode: AFK
blocked_by: []
---

# Reset stale excluded projection after candidate change

## Artifact Graph
- Artifact ID: `artifact:fpr-01-reset-stale-excluded-projection-after-candidate-change`
- Role: `ticket`
- Parent: [stale excluded final-tree projection diagnostic](../../specs/ticket-autopilot-stale-excluded-final-tree-projection-diagnostic.md)

## Parent Spec
[stale excluded final-tree projection diagnostic](../../specs/ticket-autopilot-stale-excluded-final-tree-projection-diagnostic.md)

## What to Build
Fix the canonical stale-delivery-preparation reset so candidate-bound final-tree projection state is archived and cleared even when `delivery.prepared` has never been recorded. The implementation must support the normal cycle: simplify, persist an enabled excluded projection for generation 1, fail review, adopt a changed implementation candidate at generation 2, simplify again, and record a fresh projection instead of raising `persisted final-tree projection exclusion is stale`.

Derive the old semantic identity from the complete candidate-bearing preparation set rather than using `prepared` as the sole existence guard. Preserve the current prepared-delivery path. If multiple receipts supply identity they must agree; malformed or contradictory state fails before mutation. Archive every present `STALE_DELIVERY_PREPARATION_STEPS` receipt and retain the existing deterministic reset event/history semantics.

## Acceptance Criteria
- [ ] A plan-only excluded final-tree projection is recognized as candidate-bound preparation when `delivery.prepared` is absent.
- [ ] When its semantic candidate differs, reset archives the exact old projection, clears the current slot, records old/new CandidateRefs and current artifact generation, and returns `True`.
- [ ] The end-to-end regression simplify → excluded plan → review fail → changed implementation candidate → simplify proceeds without stale-exclusion failure and can persist a generation-2 plan.
- [ ] Same-candidate reset is idempotent, returns `False`, and preserves the current plan.
- [ ] Prepared-delivery reset behavior and all existing stale preparation steps remain unchanged.
- [ ] Multiple candidate-bearing receipts with contradictory identities and plan-only malformed identities fail closed with zero partial mutation.
- [ ] Existing schema-4 ledgers need no bulk rewrite; a valid stale plan-only state converges through the normal reset transition.
- [ ] Kernel, finalizer/orchestration, CLI, and focused final-tree tests prove the causal path, followed by the full Ticket Autopilot suite.

## Frontier
Ready and AFK. The diagnosis and expected state transition are complete; no product, provider, or human decision is required.

## Step-by-Step Implementation Plan
1. Inventory every entry in `STALE_DELIVERY_PREPARATION_STEPS` and identify which receipts carry semantic candidate identity. Checkpoint: plan-only exclusion and prepared delivery are both represented.
2. Refactor `reset_stale_delivery_preparation()` to select and validate one consistent old semantic identity without treating `prepared` absence as an empty state.
3. Reuse the existing receipt archive, clearing, and event path for every stale candidate-bearing shape. Checkpoint: history contains the exact projection receipt and current state no longer does.
4. Add direct unit tests for plan-only stale, same-candidate, malformed, contradictory, and existing prepared cases.
5. Add the full review-failure retry regression through the ordinary runner/finalizer boundary and run focused plus full suites.

## Testing Plan
Automated causal tests must first reproduce the exact stale error on the old behavior, then pass after the fix. Assert artifact-generation changes, CandidateRefs, preparation history, current delivery keys, event payload, transaction rollback, and successful generation-2 simplify/projection. Run the focused final-tree projection, kernel, finalizer, and CLI tests and the full Ticket Autopilot suite.

No live provider mutation is needed. Existing provider, merge, reconciliation, and completion behavior is regression scope only and must not be claimed from local tests beyond the covered boundary.

## Out of Scope
- Changing final-tree eligibility or disabling projection.
- Adding synthetic `delivery.prepared` records.
- Directly editing active ledgers.
- Merge, reconciliation, wiki, Pi, or historical gate-reason changes.
