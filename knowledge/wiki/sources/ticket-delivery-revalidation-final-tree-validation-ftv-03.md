---
type: source
title: "Run One Final Quality Cycle on the Exact Delivery Tree"
identity_key: ticket:delivery-revalidation-final-tree-validation/FTV-03
identity_strength: stable
source_path: docs/tickets/delivery-revalidation-final-tree-validation/done/03-run-one-final-quality-cycle.md
source_digest: sha256:85f5cc79b929fec9cf0ccbb153dd1151b708fec0cf0d01945ce0c47f1c62956b
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-02
created_provenance: git-commit
disposition_changed: 2026-09-02
disposition_changed_provenance: git-rename
run_id: delivery-revalidation-final-tree-validation-20260902
---

# Run One Final Quality Cycle on the Exact Delivery Tree

Compiled from `docs/tickets/delivery-revalidation-final-tree-validation/done/03-run-one-final-quality-cycle.md`. Identity is `ticket:delivery-revalidation-final-tree-validation/FTV-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-02** via `git-commit`
- Disposition changed: **2026-09-02** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-revalidation-final-tree-validation-decision]]
- Blocked by: [[sources/ticket-delivery-revalidation-final-tree-validation-ftv-02]] — `ticket:delivery-revalidation-final-tree-validation/FTV-02`

## Run

Completed under autopilot run `delivery-revalidation-final-tree-validation-20260902`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-revalidation-final-tree-validation-ftv-03.md","payload_bytes":4183,"payload_sha256":"85f5cc79b929fec9cf0ccbb153dd1151b708fec0cf0d01945ce0c47f1c62956b"}],"payload_bytes":4183,"payload_sha256":"85f5cc79b929fec9cf0ccbb153dd1151b708fec0cf0d01945ce0c47f1c62956b","schema":1,"source_digest":"sha256:85f5cc79b929fec9cf0ccbb153dd1151b708fec0cf0d01945ce0c47f1c62956b","source_identity":"ticket:delivery-revalidation-final-tree-validation/FTV-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4183,"payload_sha256":"85f5cc79b929fec9cf0ccbb153dd1151b708fec0cf0d01945ce0c47f1c62956b","schema":1,"source_digest":"sha256:85f5cc79b929fec9cf0ccbb153dd1151b708fec0cf0d01945ce0c47f1c62956b","source_identity":"ticket:delivery-revalidation-final-tree-validation/FTV-03"} -->
```markdown
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

```
