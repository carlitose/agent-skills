---
ticket_schema: 1
ticket_id: "CB-01"
execution_mode: AFK
blocked_by: []
---

# Compact the runner contract within the existing context ceiling

## Artifact Graph

- Artifact ID: `artifact:cb-01-compact-runner-contract-within-ceiling`
- Role: `ticket`
- Parent: [ticket-autopilot context contract drift diagnostic](../../specs/ticket-autopilot-context-contract-drift-diagnostic.md)

## Parent Spec

[Ticket-autopilot context contract drift diagnostic](../../specs/ticket-autopilot-context-contract-drift-diagnostic.md)

## What to Build

Simplify `ticket-autopilot/SKILL.md` without changing behavior until the workflow fits the
existing 166,002-byte composed context ceiling and the skill fits its 130-line limit. Then
refresh the exact controlled baseline and operator guide from the measured compacted artifact.

## Acceptance Criteria

- [ ] `ticket-autopilot/SKILL.md` remains behaviorally complete for authority, lifecycle,
      bounded leaves, CandidateRef drift, verification, reconciliation, delivery, merge,
      docs-only, wiki-sync, gates, and final reporting.
- [ ] The skill has at most 130 lines and the controlled workflow report has
      `ceiling.status == "within"` against the unchanged 166,002-byte ceiling.
- [ ] The workflow closure is reduced by at least 1,195 bytes from the diagnosed 54,541-byte
      state, or an equally strong measured margin keeps the composed total within the ceiling.
- [ ] `test_context_budget.py` and `docs/autopilot-context-cost-guide.md` quote the exact same
      newly measured listing, closure, static-prefix, and composed values.
- [ ] No ceiling value, evidence class, authorization boundary, or failure/gate condition is
      weakened to make the tests pass.
- [ ] Skill graph, context-budget, model-invocation policy, context-passing, wiki-sync,
      reconciliation, delivery, and full runner suites pass.

## Frontier

Ready. The responsible file, exact byte/line deltas, unchanged ceiling, and prohibited
shortcuts are pinned in the diagnostic spec.

## Step-by-Step Implementation Plan

1. Freeze instruction-boundary tests and current required semantics before editing the skill.
2. Consolidate repeated scheduler, reconciliation, and wiki-sync prose while retaining every
   normative rule and reference.
3. Measure the controlled closure and iterate until both the byte ceiling and line limit pass.
4. Update the exact baseline assertions and guide from the final measurement.
5. Run causal boundary modules and the full runner suite, then compare the final skill against
   the pre-compaction contract for semantic omissions.

## Testing Plan

Run the context-budget and skill-graph tests first, then model-invocation policy,
context-passing, leaf protocol/budget, reconciliation, delivery/finalizer, wiki-sync, and full
ticket-autopilot suites. Record exact before/after bytes, words, lines, total, ceiling delta,
and the unchanged ceiling configuration.

## Out of Scope

- Raising, removing, or bypassing the 166,002-byte ceiling.
- Removing shipped runner capabilities or safety contracts.
- Changing executable runner behavior.
- Changing any skill's model-invocation classification.
