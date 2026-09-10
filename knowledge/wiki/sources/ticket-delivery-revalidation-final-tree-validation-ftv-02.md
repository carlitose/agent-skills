---
type: source
title: "Persist and Recover Projected-Not-Integrated Completion"
identity_key: ticket:delivery-revalidation-final-tree-validation/FTV-02
identity_strength: stable
source_path: docs/tickets/delivery-revalidation-final-tree-validation/done/02-persist-and-recover-projected-state.md
source_digest: sha256:a42a693008d07e1712073f01343214b656fe8bc6ae873c148db2333ed459ebb2
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-02
created_provenance: git-commit
disposition_changed: 2026-09-02
disposition_changed_provenance: git-rename
run_id: delivery-revalidation-final-tree-validation-20260902
---

# Persist and Recover Projected-Not-Integrated Completion

Compiled from `docs/tickets/delivery-revalidation-final-tree-validation/done/02-persist-and-recover-projected-state.md`. Identity is `ticket:delivery-revalidation-final-tree-validation/FTV-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-02** via `git-commit`
- Disposition changed: **2026-09-02** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-revalidation-final-tree-validation-decision]]
- Blocked by: [[sources/ticket-delivery-revalidation-final-tree-validation-ftv-01]] — `ticket:delivery-revalidation-final-tree-validation/FTV-01`

## Run

Completed under autopilot run `delivery-revalidation-final-tree-validation-20260902`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-revalidation-final-tree-validation-ftv-02.md","payload_bytes":3869,"payload_sha256":"a42a693008d07e1712073f01343214b656fe8bc6ae873c148db2333ed459ebb2"}],"payload_bytes":3869,"payload_sha256":"a42a693008d07e1712073f01343214b656fe8bc6ae873c148db2333ed459ebb2","schema":1,"source_digest":"sha256:a42a693008d07e1712073f01343214b656fe8bc6ae873c148db2333ed459ebb2","source_identity":"ticket:delivery-revalidation-final-tree-validation/FTV-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3869,"payload_sha256":"a42a693008d07e1712073f01343214b656fe8bc6ae873c148db2333ed459ebb2","schema":1,"source_digest":"sha256:a42a693008d07e1712073f01343214b656fe8bc6ae873c148db2333ed459ebb2","source_identity":"ticket:delivery-revalidation-final-tree-validation/FTV-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "FTV-02"
execution_mode: AFK
blocked_by:
  - "FTV-01"
---

# Persist and Recover Projected-Not-Integrated Completion

## Artifact Graph

- Artifact ID: `artifact:delivery-revalidation-projected-state`
- Role: `ticket`
- Parent: [Final-Tree Validation Architecture Decision](../../specs/delivery-revalidation-final-tree-validation-decision.md)

## Parent Spec

[Final-Tree Validation Architecture Decision](../../specs/delivery-revalidation-final-tree-validation-decision.md)

## What to Build

Implement the spec's durable pre-quality projection transaction behind explicit `enabled` mode,
without yet changing automatic final-quality scheduling. For an exact eligible manifest, persist
intent before effects, apply the same-byte/same-mode move, canonical completion receipt, and full
link closure once, read every effect back, prove the complete `I -> D` diff, bind `D`, and persist
`projected-not-integrated`.

Make `intent-persisted`, `effects-read-back`, and `final-tree-bound` explicit replay checkpoints.
Exact partial states resume idempotently; exact final replay returns `already-applied`; ambiguous or
contradictory state blocks before publication. A failed or interrupted local projection never
moves the ticket back to its pending path and never becomes a completion or integration claim.

## Acceptance Criteria

- [ ] The runner persists the versioned manifest and expected source/destination/index identities
      before the first filesystem or index effect.
- [ ] The exact ticket move, receipt, and link effects each use unique immutable effect identities
      and apply at most once.
- [ ] Complete readback binds the actual final CandidateRef `D` and only then records
      `projected-not-integrated`.
- [ ] Crashes after intent, any partial effect set, effect readback, and final-tree binding resume
      from exact state without duplicate moves, receipts, links, or ledger history.
- [ ] Exact final replay returns `already-applied` and appends no second projection effect.
- [ ] Both paths present, both absent, changed bytes or mode, unexpected index rows, stale
      CandidateRefs, duplicate effect keys, changed receipts or links, and proof tampering block
      before commit, push, PR, or provider mutation.
- [ ] Disabling the feature after intent does not abandon or reinterpret that intent; replay uses
      its recorded contract version until it finishes exactly or blocks.
- [ ] Historical runs and excluded topologies retain their current lifecycle without backfilled
      checkpoints or projection state.

## Frontier

Dependency-blocked by `FTV-01`.

## Step-by-Step Implementation Plan

1. Extend the canonical manifest with durable effect and checkpoint identities owned by one
   projection transaction module.
2. Persist intent in kernel/ledger before invoking finalizer or Git-index effects.
3. Apply and read back ticket, receipt, and deterministic link operations through idempotent exact
   adapters.
4. Add `projected-not-integrated` reduction, status projection, replay, and contradiction gates.
5. Preserve literal history and contract-version binding across compaction, resume, and mode
   rollback.

## Testing Plan

- State-machine tests that crash at each checkpoint and after each individual effect.
- Mutation tests for path, blob, mode, receipt, link closure, index stages, CandidateRef, effect
  identity, and contract version.
- Replay tests for exact partial, exact complete, ambiguous, tampered, and historical states.
- Integration tests in disposable repositories proving no commit, branch publication, PR, or
  provider call occurs before final-tree binding.

## Out of Scope

- Automatically selecting this transaction in the scheduler.
- Running final review, QA, or verification on `D`.
- Changing the default from `observe`.
- Repairing an unrelated historical run.

```
