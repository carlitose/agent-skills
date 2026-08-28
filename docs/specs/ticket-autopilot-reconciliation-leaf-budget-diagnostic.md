# Ticket Autopilot Reconciliation Leaf-Budget Exhaustion Bug

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-reconciliation-leaf-budget-diagnostic`
- Role: `spec`
- Standalone: true

### Children

- [LB-01 restore semantic-revalidation leaf capacity](../tickets/ticket-autopilot-reconciliation-leaf-budget/done/01-restore-semantic-revalidation-leaf-capacity.md)

## Type

Diagnostic spec

## Status

Fixed and covered by regression tests in LB-01.

## Diagnosis Report - lens: single-pass

### Root cause

Semantic reconciliation correctly invalidated review, QA, and verification evidence, but
`Kernel._invalidate_leaf_artifacts()` cleared handoffs/results while retaining the prior
CandidateRef's interaction counters and consumed mandatory reservations. A previously
verified ticket could therefore enter a fresh verification cycle with no usable reservation.
The contradiction was between `Kernel.prepare_reconciliation()` and
`leaf_protocol._admit_resources()`.

### Evidence

- The affected WS-04 run entered reconciliation with 7 of 10 interactions consumed and both
  mandatory reservations complete.
- Revalidation retained those counters, then fresh review, QA planning, and QA execution
  reached 10 of 10.
- The canonical verification checkpoint completed bundle construction, validation,
  reduction, and handoff in memory, but admission failed with
  `leaf interaction budget is reserved for mandatory stages`.
- An in-memory replay reproduced the same exception without mutating the ledger.
- The CandidateRef passed 157 LLM Wiki tests, 33 focused runner/skill tests, compilation,
  patch-integrity, and patch-equivalence checks before the admission failure.

### Fix

Budget enforcement now applies to the current semantic CandidateRef epoch. Every semantic
invalidation starts a fresh bounded epoch and clears old mandatory-reservation consumption;
append-only `leaf-result-recorded` history remains the source for truthful lifetime resource
reporting. Equivalent reconciliation keeps its evidence and consumes no capacity.

Existing schema-4 runs use the public `revalidation-budget-repair` transition. It rebuilds
the current epoch from retained CandidateRef-bound progress, records before/after state and
source event sequences, is idempotent, and refuses to erase same-CandidateRef retries. Real
exhaustion is persisted as an actionable `resource-budget` gate.

### Alternatives ruled out

- **Project failure:** candidate-scoped tests and integrity checks passed.
- **Stale bundle or CandidateRef:** checkpoint work reached `handoff-ready` for the exact
  current CandidateRef before budget admission.
- **Missing reservation configuration:** both slots existed, but belonged to the old epoch.
- **Manual ledger repair:** rejected because it bypasses audited transition replay.
- **Reusing old evidence:** rejected because a changed CandidateRef requires fresh validation.

### Confidence: high

The live failure, in-memory replay, persisted history, old admission arithmetic, and passing
post-fix 7-of-10 regression all identify the same mechanism.

## Preserved constraints

- Changed CandidateRefs receive fresh review, QA execution, verification, and merge
  authorization.
- Same-CandidateRef retries remain hard-bounded.
- Lifetime interaction, tool-call, wall-time, invalidation, cache, and failure reporting stays
  truthful.
- Exact-head merge authorization, provider readback, and verification claims are unchanged.
