---
ticket_schema: 1
ticket_id: "06"
execution_mode: HITL
blocked_by:
  - "05"
---

# Decide whether evidence may survive CandidateRef changes

## Parent Spec

[bounded-ticket-autopilot-leaf-protocol.md](../../specs/bounded-ticket-autopilot-leaf-protocol.md)

## What to Build

Run a focused grilling decision on issue #9's proposed selective invalidation. Decide
whether to preserve accepted decision D6 unchanged or replace it with a precise,
fail-closed causal reuse contract.

## Acceptance Criteria

- [ ] The decision compares global invalidation with concrete selective-reuse alternatives
      for review, QA plan, QA execution, verification, static environment facts, live
      evidence, and merge authorization.
- [ ] Each alternative names authorization, causal scope proof, cache identity, stale-result
      attack cases, failure behavior, and implementation cost.
- [ ] The analysis demonstrates whether the same real blocker and should-fix from issue #9
      would still be discovered after a candidate mutation.
- [ ] Human authority explicitly chooses to preserve D6 or accepts exact replacement rules;
      silence or a broad performance goal is not authorization.
- [ ] If D6 is preserved, the decision records why same-CandidateRef caching is the safe
      optimization ceiling.
- [ ] If D6 changes, a decision spec records the new invariant and Wayfinder emits separate
      implementation and integrated forward-test tickets.
- [ ] Merge authorization remains bound to the current PR head SHA in every alternative.
- [ ] No missing live evidence or partial inspection can survive as a stronger claim.

## Frontier

Exact human decision required. Dependency-blocked by `05` so the decision uses measured
same-CandidateRef savings before considering a weaker invalidation boundary.

## Step-by-Step Implementation Plan

1. Present current D6, observed repeated-work costs, and measured safe cache gains.
2. Enumerate artifact categories and candidate-change examples.
3. Stress-test causal independence, hidden callers, generated artifacts, environment drift,
   and claim propagation.
4. Compare preserve-D6, limited non-semantic carry-forward, and semantic selective-reuse
   contracts.
5. Obtain an explicit human decision and record rationale, rejected alternatives, and
   consequences.
6. Update the Wayfinder frontier and emit only the tickets authorized by that decision.

## Testing Plan

- Tabletop adversarial scenarios for stale findings, partial diffs, shared callers, changed
  tests, changed ticket acceptance, provider receipts, and PR-head drift.
- Prototype or fixture evidence where reasoning alone cannot establish causal independence.
- No code implementation or claim elevation occurs in this ticket.

## Out of Scope

- Implementing selective invalidation before the decision.
- Treating file-path non-overlap as sufficient causal proof.
- Weakening exact-SHA authorization or live-evidence gates.
