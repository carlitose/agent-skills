---
ticket_schema: 1
ticket_id: "FTV-01"
execution_mode: AFK
blocked_by: []
---

# Observe Exact Tracked Completion Projections

## Artifact Graph

- Artifact ID: `artifact:delivery-revalidation-final-tree-observation`
- Role: `ticket`
- Parent: [Final-Tree Validation Architecture Decision](../../specs/delivery-revalidation-final-tree-validation-decision.md)

## Parent Spec

[Final-Tree Validation Architecture Decision](../../specs/delivery-revalidation-final-tree-validation-decision.md)

## What to Build

Implement the spec's eligibility contract and observation-first rollout as one non-authoritative
vertical slice. Add a versioned canonical manifest for a prospective ordinary tracked `I -> D`
completion, including the exact ticket move, receipt, complete link-repoint closure, sorted
path/blob/mode diff, negative extra-diff proof, CandidateRefs, effect keys, and contract version.

Add explicit `off`, `observe`, and `enabled` configuration parsing, but default this slice to
`observe`. In observation mode, compute the prospective lane without changing the current full
lifecycle, then compare the eventual authoritative delivery candidate and effects with the planned
manifest. Persist a content-addressed observation or discrepancy that cannot satisfy a quality,
completion, provider, or merge gate.

## Acceptance Criteria

- [ ] `observe` is the initial default; unknown or malformed mode configuration fails closed.
- [ ] One exact ordinary tracked fixture yields a deterministic versioned manifest binding `I`,
      planned `D`, ticket bytes and mode, canonical receipt, complete link closure, complete diff,
      negative proof, and unique effects.
- [ ] Reordering inputs or replaying the same input yields byte-identical manifest and observation
      identities without duplicate ledger effects.
- [ ] Extra paths, changed implementation blobs, ticket bytes or mode, receipt fields, unapproved
      or missed eligible links, stale CandidateRefs, duplicate effects, ignored/external sources,
      reconciliation, recovery, and provider mutation cannot classify as eligible.
- [ ] Observation mode leaves the existing implementation-tree verification and delivery
      revalidation lifecycle authoritative and records parity or discrepancy only after exact
      actual-`D` readback.
- [ ] Observation artifacts visibly declare that they grant no completion, provider, merge,
      terminal, wiki, Pi, status-change, or cleanup authority.
- [ ] Historical ledger reduction accepts events without this optional observation and never
      fabricates one.

## Frontier

Ready. This is the first production slice and changes no authoritative delivery ordering.

## Step-by-Step Implementation Plan

1. Add one owner module for canonical manifest planning, encoding, validation, digesting, and full
   negative-diff comparison.
2. Add strict mode configuration and immutable observation/discrepancy ledger events.
3. Invoke the observer at the current tracked completion boundary without changing scheduler
   readiness or finalizer effects.
4. Compare the prospective and authoritative `D` only after exact current-path readback.
5. Expose bounded status output for diagnostics while keeping every existing authority projection
   unchanged.

## Testing Plan

- Unit tests for canonical encoding, ordering, complete link closure, diff completeness, tampering,
  duplicate effects, stale identity, and strict mode parsing.
- Kernel/ledger tests for observation append, replay, discrepancy, compaction, and historical
  events with no manifest.
- CLI/finalizer integration tests proving `observe` leaves current stage order and provider state
  unchanged.
- Port the DRV-02 17-fixture outcome matrix into production-contract tests without treating the
  disposable prototype's hashes as Git object IDs.

## Out of Scope

- Applying completion before final quality.
- Adding `projected-not-integrated` as an authoritative lifecycle state.
- Reusing review, QA, or verification evidence.
- Enabling the narrow lane by default.
