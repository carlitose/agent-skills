---
type: source
title: "Store ledger history as verifiable state deltas"
identity_key: ticket:ticket-autopilot-ledger-history-size/LHS-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-ledger-history-size/done/01-store-history-as-verifiable-state-deltas.md
source_digest: sha256:ad4041eb0f9c71828bed173fd03bb4bdc222a5ba1d1ef93a49e37f7937cba039
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-29
created_provenance: git-commit
disposition_changed: 2026-08-29
disposition_changed_provenance: git-rename
run_id: lhs-ledger-history-20260829
---

# Store ledger history as verifiable state deltas

Compiled from `docs/tickets/ticket-autopilot-ledger-history-size/done/01-store-history-as-verifiable-state-deltas.md`. Identity is `ticket:ticket-autopilot-ledger-history-size/LHS-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-29** via `git-commit`
- Disposition changed: **2026-08-29** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-ledger-history-size-diagnostic]]

## Run

Completed under autopilot run `lhs-ledger-history-20260829`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-ledger-history-size-lhs-01.md","payload_bytes":3654,"payload_sha256":"ad4041eb0f9c71828bed173fd03bb4bdc222a5ba1d1ef93a49e37f7937cba039"}],"payload_bytes":3654,"payload_sha256":"ad4041eb0f9c71828bed173fd03bb4bdc222a5ba1d1ef93a49e37f7937cba039","schema":1,"source_digest":"sha256:ad4041eb0f9c71828bed173fd03bb4bdc222a5ba1d1ef93a49e37f7937cba039","source_identity":"ticket:ticket-autopilot-ledger-history-size/LHS-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3654,"payload_sha256":"ad4041eb0f9c71828bed173fd03bb4bdc222a5ba1d1ef93a49e37f7937cba039","schema":1,"source_digest":"sha256:ad4041eb0f9c71828bed173fd03bb4bdc222a5ba1d1ef93a49e37f7937cba039","source_identity":"ticket:ticket-autopilot-ledger-history-size/LHS-01"} -->
```markdown
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

```
