---
ticket_schema: 1
ticket_id: "DRV-02"
execution_mode: AFK
blocked_by:
  - "DRV-01"
---

# Prototype projection-proof options

## Artifact Graph
- Artifact ID: `ticket:delivery-revalidation-efficiency:DRV-02`
- Role: `ticket`
- Parent: [Delivery revalidation efficiency wayfinder](../../specs/delivery-revalidation-efficiency-wayfinder.md)

## Parent Spec
[Delivery revalidation efficiency wayfinder](../../specs/delivery-revalidation-efficiency-wayfinder.md)

## What to Build
Build a throwaway, standard-library-only model comparing three unselected architectures: completion projection before the final quality cycle, proof-carrying deterministic projection after implementation verification, and a bounded hybrid.

The prototype must model exact trees, blobs, modes, ticket bytes, receipts, link repoints, artifact generations, evidence segments, budgets, crash checkpoints, and replay. It must fail closed for arbitrary or ambiguous drift and leave only durable findings in the parent map or its research report.

## Acceptance Criteria
- [ ] All three candidate designs share the same explicit state/effect fixtures.
- [ ] Positive fixtures cover exact tracked move, same-byte/mode ticket, canonical receipt, approved link repoints, and negative extra-diff proof.
- [ ] Negative fixtures cover extra path/blob/mode changes, changed receipt fields, stale CandidateRef, tampered proof, duplicate effects, ignored-source drift, reconciliation drift, provider mutation, and crash ambiguity.
- [ ] Each design reports lifecycle truthfulness, recovery complexity, proof surface, test-selection risk, compatibility impact, command avoidance, and residual full-revalidation cases.
- [ ] Prototype code and state are deleted; only reproducible contract, results, cleanup proof, and limitations persist.
- [ ] No production architecture is selected.

## Frontier
Blocked by DRV-01. Its output unblocks DRV-03.

## Step-by-Step Implementation Plan
1. Derive fixtures and invariants from DRV-01 rather than inventing a parallel lifecycle.
2. Freeze expected outcomes before implementing the model.
3. Run all designs against identical positive, negative, crash, and replay matrices.
4. Measure proof complexity and avoided work without calling providers or mutating real runs.
5. Delete the prototype and fold the labeled results into the durable frontier evidence.

## Testing Plan
- Unit-test every fixture and exact digest transition.
- Use mutation-style negatives to prove one extra effect forces full revalidation.
- Verify deterministic replay and crash recovery for every checkpoint.
- Confirm no prototype files, caches, generated state, or run-ledger drift remains.

## Out of Scope
- Production code or migration.
- Live provider mutation.
- Choosing a design or test threshold.
- General test-impact analysis outside deterministic completion projection.
