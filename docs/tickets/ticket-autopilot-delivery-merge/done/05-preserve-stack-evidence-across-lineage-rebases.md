---
ticket_schema: 1
ticket_id: "05"
execution_mode: AFK
blocked_by:
  - "02"
---

# Preserve stack evidence across lineage-only rebases

## Parent Spec

[ticket-autopilot-autonomous-stacked-delivery.md](../../specs/ticket-autopilot-autonomous-stacked-delivery.md)

## What to Build

Separate semantic candidate identity from Git delivery lineage and use that boundary during
single-parent stack reconciliation. A parent merge that changes commit SHAs but preserves
the exact base tree, child tree, and ticket contract must not rerun code review, QA, or
verification. Any semantic change must retain the existing fail-closed invalidation path.

## Acceptance Criteria

- [ ] Semantic candidate contract v2 binds exactly to base tree OID, candidate tree OID,
      normalized ticket digest, and contract version; provider/PR/base/head lineage is a
      separate versioned record.
- [ ] Leaf handoffs, cache entries, QA/verification artifacts, checkpoints, ledger replay,
      and reports consistently bind to the semantic candidate rather than a mutable commit
      lineage SHA.
- [ ] Reconciliation derives the new base and child tree OIDs from local Git state after a
      guarded rebase; caller-supplied equivalence claims are forbidden.
- [ ] Exact old/new semantic equality preserves validated stages, semantic leaf artifacts,
      cache identity, artifact generation, and claim ceiling without invoking review,
      QA-plan, QA-execute, or verify again.
- [ ] A changed base tree, candidate tree, ticket digest, or contract version clears all
      semantic artifacts and returns `revalidation-required` at the normal review boundary.
- [ ] Every reconciliation records old/new semantic refs, old/new heads, target base, and
      the deterministic equivalence/invalidation result in replay-valid ledger history.
- [ ] Remote divergence, rebase conflict, tree-resolution failure, and retarget/readback
      contradiction remain durable gates and never preserve evidence optimistically.
- [ ] A changed PR head always clears a one-shot manual merge authorization even when the
      semantic candidate is equal.
- [ ] Incompatible active ledgers or candidate contracts fail with an actionable version
      error; no silent legacy interpretation or hand-maintained alternate parser is added.
- [ ] A three-ticket stack test proves lineage-only parent merges do not increase semantic
      review counts, while planted base, child, and ticket drift each force complete
      revalidation and rediscover their findings.

## Frontier

Dependency-blocked by ticket `02`. The immediate expected-head merge critical path and its
replay receipts must be stable before stack reconciliation changes the identity feeding it.

## Step-by-Step Implementation Plan

1. Introduce semantic candidate v2 and delivery-lineage contracts with one canonical
   serializer/validator path; version ledger and downstream artifact bindings explicitly.
2. Update candidate construction for uncommitted implementation and committed rebased
   branches so both resolve base/candidate tree OIDs correctly.
3. Refactor kernel, leaf, cache, QA, verification, and reporting bindings around the semantic
   identity while keeping merge authorization tied to delivery head.
4. Add a deterministic stack-equivalence transition that preserves semantic state only on
   exact ref equality and records a complete causal receipt.
5. Integrate the transition into guarded rebase, force-with-lease push, retarget, and live
   provider readback without adding an agent-authored semantic judgment.
6. Add compatibility errors and the full unit, ledger replay, Git integration, and stacked
   forward-test matrix.

## Testing Plan

Run ticket-autopilot, verification-audit, skill-graph, and forward-test suites. Add isolated
Git fixtures for fast-forward, squash-equivalent, merge-commit-equivalent, unrelated base
advance, merge resolution, child amendment, conflict, dropped commit, generated-file drift,
ticket drift, force-with-lease failure, and crash/replay. Assert leaf invocation counts and
artifact identities, not only final states.

## Out of Scope

- Path-based, dependency-graph, or agent-asserted selective evidence reuse.
- Autonomous merge authority; ticket `06` owns that policy.
- Preserving a one-shot manual authorization after any head change.
- Live-provider readiness claims without disposable credentialed evidence.
