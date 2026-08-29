---
ticket_schema: 1
ticket_id: "LHS-01"
execution_mode: AFK
blocked_by: []
---

# Store ledger history as verifiable state deltas

## Artifact Graph

- Artifact ID: `artifact:lhs-01-store-history-as-verifiable-state-deltas`
- Role: `ticket`
- Parent: [Ledger History Size Diagnostic](../../specs/ticket-autopilot-ledger-history-size-diagnostic.md)

## Parent Spec

[Ledger History Size Diagnostic](../../specs/ticket-autopilot-ledger-history-size-diagnostic.md)

## What to Build

Replace repeated full snapshots in newly sealed ledger history with deterministic state deltas
that reconstruct the same snapshots and validate against the existing event hash chain. Keep
legacy full histories readable and add an explicit atomic command to compact a validated existing
ledger without changing its semantic audit identities.

## Acceptance Criteria

- [ ] The first compact-history event contains a full checkpoint; later events contain canonical
      state deltas rather than full snapshot copies.
- [ ] Delta application reconstructs the exact snapshot used to compute each existing event hash,
      and the final reconstructed snapshot equals the persisted current state.
- [ ] Event sequence, details, `previous_hash`, original `hash`, and final history head are
      unchanged when a full history is compacted.
- [ ] Existing all-full schema-4 histories load unchanged; a full prefix followed by a compact
      suffix loads and validates; a full event after the compact suffix fails closed.
- [ ] Dictionary add/remove/replace, append-only list growth, non-append list replacement, escaped
      path components, empty deltas, malformed operations, and semantic corruption have tests.
- [ ] An explicit CLI compaction command validates before mutation, writes atomically, is
      idempotent, and leaves the original bytes unchanged on validation or write failure.
- [ ] A growing multi-ticket fixture shows compact history is materially smaller and grows with
      changes rather than repeated full state; the test records both byte counts.
- [ ] Evidence, PR bodies, approvals, CandidateRefs, gates, receipts, and current run state remain
      byte-for-byte equivalent after reconstruction.
- [ ] The complete ticket-autopilot tests and forward-test workflow pass.

## Frontier

Ready. Real ledgers demonstrate that embedded snapshots account for more than 99% of the largest
file while exact-snapshot deduplication has negligible leverage.

## Step-by-Step Implementation Plan

1. Add red tests for structural diff/apply, compact hash-chain replay, corruption, and growth.
2. Implement a small deterministic snapshot-delta codec inside the ledger boundary.
3. Seal new events with a full first checkpoint and a compact suffix while hashing the
   reconstructed original event shape.
4. Extend ledger validation to accept legacy full history or one-way compact suffix and run the
   existing transition validator on reconstructed snapshots.
5. Add an explicit locked, atomic, idempotent compaction command for existing validated ledgers.
6. Run focused ledger/kernel tests, size regression, complete runner suite, and forward test.

## Testing Plan

Use only disposable ledger fixtures for mutation tests. Compare canonical reconstructed
snapshots and original hashes, inject corrupt patches and write failures, assert unchanged source
bytes on failure, and report full versus compact serialized size.

## Out of Scope

- Automatically compacting historical ledgers without an explicit command.
- Deleting audit events or moving trust to an unverified external database.
- Redacting or reclassifying existing evidence as part of the size fix.
