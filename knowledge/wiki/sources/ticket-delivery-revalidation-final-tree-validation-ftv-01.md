---
type: source
title: "Observe Exact Tracked Completion Projections"
identity_key: ticket:delivery-revalidation-final-tree-validation/FTV-01
identity_strength: stable
source_path: docs/tickets/delivery-revalidation-final-tree-validation/done/01-observe-exact-tracked-completion-projections.md
source_digest: sha256:58e0408a133f9559e5a9e8ff3cd5b60fd06289d2a2983b7ff5fd1aa5637f846d
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-02
created_provenance: git-commit
disposition_changed: 2026-09-02
disposition_changed_provenance: git-rename
run_id: delivery-revalidation-final-tree-validation-20260902
---

# Observe Exact Tracked Completion Projections

Compiled from `docs/tickets/delivery-revalidation-final-tree-validation/done/01-observe-exact-tracked-completion-projections.md`. Identity is `ticket:delivery-revalidation-final-tree-validation/FTV-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-02** via `git-commit`
- Disposition changed: **2026-09-02** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-revalidation-final-tree-validation-decision]]

## Run

Completed under autopilot run `delivery-revalidation-final-tree-validation-20260902`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-revalidation-final-tree-validation-ftv-01.md","payload_bytes":4047,"payload_sha256":"58e0408a133f9559e5a9e8ff3cd5b60fd06289d2a2983b7ff5fd1aa5637f846d"}],"payload_bytes":4047,"payload_sha256":"58e0408a133f9559e5a9e8ff3cd5b60fd06289d2a2983b7ff5fd1aa5637f846d","schema":1,"source_digest":"sha256:58e0408a133f9559e5a9e8ff3cd5b60fd06289d2a2983b7ff5fd1aa5637f846d","source_identity":"ticket:delivery-revalidation-final-tree-validation/FTV-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4047,"payload_sha256":"58e0408a133f9559e5a9e8ff3cd5b60fd06289d2a2983b7ff5fd1aa5637f846d","schema":1,"source_digest":"sha256:58e0408a133f9559e5a9e8ff3cd5b60fd06289d2a2983b7ff5fd1aa5637f846d","source_identity":"ticket:delivery-revalidation-final-tree-validation/FTV-01"} -->
```markdown
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

```
