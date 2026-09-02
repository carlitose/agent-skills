---
ticket_schema: 1
ticket_id: "FTV-03"
execution_mode: AFK
blocked_by:
  - "FTV-02"
---

# Run One Final Quality Cycle on the Exact Delivery Tree

## Artifact Graph

- Artifact ID: `artifact:delivery-revalidation-single-final-cycle`
- Role: `ticket`
- Parent: [Final-Tree Validation Architecture Decision](../../specs/delivery-revalidation-final-tree-validation-decision.md)

## Parent Spec

[Final-Tree Validation Architecture Decision](../../specs/delivery-revalidation-final-tree-validation-decision.md)

## What to Build

Connect the eligible ordinary tracked transaction to scheduler execution under explicit
`enabled` mode. After implementation and simplification freeze implementation CandidateRef `I`,
select the lane before final quality, create and bind exact delivery CandidateRef `D`, then run
`review -> qa-plan -> qa-execute -> verify -> finalize` exactly once against `D`.

Keep the current full lifecycle unchanged for every preflight exclusion. Never import review, QA,
or verification results from `I`. Preserve implementation and simplification only as explicit
predecessor lineage, while every final record, rendered body, provider head, expected-head merge,
and terminal proof binds `D` through their existing contracts.

## Acceptance Criteria

- [ ] An exact eligible tracked ticket in explicit `enabled` mode reaches
      `projected-not-integrated` before review and records one review, one QA plan, one QA execution,
      one verification, and one finalization generation, all bound to `D`.
- [ ] No review, QA, or verification result for `I` satisfies a stage or claim for `D`.
- [ ] An ineligible preflight case follows the existing full process without a new projection
      intent or altered historical event.
- [ ] A review, QA, verification, or finalization failure keeps `D` local, publishes nothing, keeps
      the original ticket active, and resumes the failed causally required stage against the same
      `D`.
- [ ] Semantic candidate drift after projection invalidates to `implement`; projection-only
      contradiction enters exact recovery. Neither path moves the ticket back to pending.
- [ ] Commit, PR body, provider head, expected-head merge, and fresh terminal proof reject any
      CandidateRef or tree other than the verified `D`.
- [ ] Tracked-exception, ignored/external, recovery, reconciliation, provider-before/after,
      historical-ledger, wiki, Pi, status, and cleanup matrices preserve their existing behavior
      and separate authority gates.
- [ ] A defect discovered after terminal integration is represented by a linked follow-up ticket,
      not by rewriting the completed source or ledger.

## Frontier

Dependency-blocked by `FTV-02`.

## Step-by-Step Implementation Plan

1. Add exact scheduler readiness for the eligible lane after simplification and before review.
2. Drive the existing projection transaction to `D` and bind the active quality generation to
   that CandidateRef.
3. Update invalidation and failure reduction so final stages resume on `D`, while semantic drift
   returns to implementation without path rollback.
4. Reduce the final Verification Record from direct `D` review/QA/verification and explicit `I`
   predecessor lineage only.
5. Exercise provider, terminal, wiki, Pi, status, and legacy boundaries to prove no authority or
   topology broadening.

## Testing Plan

- Scheduler/kernel/ledger tests for exact stage order, generation counts, failure resume, semantic
  invalidation, and no backward ticket move.
- Verification contract tests that reject imported `I` review/QA/verification and mismatched `D`
  artifacts.
- End-to-end disposable-repository tests through finalization, delivery rendering, fake-provider
  exact-head merge, and fresh terminal reachability.
- Existing full suites for ticket source, recovery, reconciliation, provider, terminal proof,
  wiki, Pi, and status-change behavior.

## Out of Scope

- Making `enabled` the default.
- General causal test selection or proof-carrying evidence composition.
- Optimizing any topology outside the exact ordinary tracked classifier.
- Granting merge, publication, or post-integration synchronization authority.
