---
ticket_schema: 1
ticket_id: "DRV-01"
execution_mode: AFK
blocked_by: []
---

# Map the completion-to-delivery revalidation flow

## Artifact Graph
- Artifact ID: `ticket:delivery-revalidation-efficiency:DRV-01`
- Role: `ticket`
- Parent: [Delivery revalidation efficiency wayfinder](../../specs/delivery-revalidation-efficiency-wayfinder.md)

### Produces
- [Delivery revalidation current-flow and cost report](../../research/delivery-revalidation-current-flow-and-cost.md)

## Parent Spec
[Delivery revalidation efficiency wayfinder](../../specs/delivery-revalidation-efficiency-wayfinder.md)

## What to Build
Complete the current-state and cost investigation seeded in the linked research report. Map the exact call graph, state transitions, effects, CandidateRefs, artifacts, budgets, replay paths, and authorities from verified implementation through completion projection, delivery revalidation, provider mutation, terminal proof, and post-integration handling.

Separate causally necessary final-tree checks from broad checks repeated only because the runner lacks a narrower proof contract. Include tracked, ignored, recovery, reconciliation, and historical-ledger cases without proposing implementation.

## Acceptance Criteria
- [ ] The report cites every owning production module and representative test family.
- [ ] A state/effect table covers normal tracked completion, ignored source, reconciliation, recovery, crash/replay, provider-before/after, and terminal proof.
- [ ] Each effect names path/blob/mode/tree/receipt/link/ledger changes and the evidence it invalidates.
- [ ] At least three completed runs are measured with a reproducible command-count and wall-time method, or unavailable samples are reported as a limitation.
- [ ] Full-revalidation false positives and must-revalidate negatives are explicit.
- [ ] The parent map is updated with durable facts and unresolved proof questions only.
- [ ] No design, test-selection policy, or production change is selected.

## Frontier
Ready. This evidence unblocks DRV-02 and DRV-03.

## Step-by-Step Implementation Plan
1. Trace finalizer, kernel, CLI, ticket-source, recovery, reconciliation, provider, and terminal-integration paths.
2. Build state/effect and evidence-invalidation tables from code and tests.
3. Measure available completed-run duplicate cycles without mutating their ledgers or artifacts.
4. Record must-revalidate counterexamples and candidate deterministic classes.
5. Update the report and fold only stable findings into the wayfinder.

## Testing Plan
- Resolve every repository citation and Artifact Graph edge.
- Run focused kernel, CLI, and ticket-source tests covering cited transitions.
- Recompute cost summaries from raw run artifacts and label missing/non-comparable samples.
- Confirm all inspected run ledgers remain byte-identical.

## Out of Scope
- Implementing a projection proof.
- Choosing among pre-projection, proof-carrying, or hybrid designs.
- Changing verification, merge, completion, reconciliation, wiki, or Pi authority.
