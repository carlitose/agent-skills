---
type: source
title: "Ticket Autopilot Stale Excluded Final-Tree Projection Reset"
identity_key: artifact:ticket-autopilot-stale-excluded-final-tree-projection-diagnostic
identity_strength: stable
source_path: docs/specs/ticket-autopilot-stale-excluded-final-tree-projection-diagnostic.md
source_digest: sha256:193da9cbe36baacda4a7ba7d71353a554742fb4997ccaf4f72c2f28ac30bd339
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Ticket Autopilot Stale Excluded Final-Tree Projection Reset

Compiled from `docs/specs/ticket-autopilot-stale-excluded-final-tree-projection-diagnostic.md`. Identity is `artifact:ticket-autopilot-stale-excluded-final-tree-projection-diagnostic`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-ticket-autopilot-stale-excluded-final-tree-projection-fpr-01]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[14],"status":"present"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[9],"status":"present"},"verification":{"headings":[13],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/artifact-ticket-autopilot-stale-excluded-final-tree-projection-diagnostic.md","payload_bytes":6391,"payload_sha256":"193da9cbe36baacda4a7ba7d71353a554742fb4997ccaf4f72c2f28ac30bd339"}],"payload_bytes":6391,"payload_sha256":"193da9cbe36baacda4a7ba7d71353a554742fb4997ccaf4f72c2f28ac30bd339","schema":1,"source_digest":"sha256:193da9cbe36baacda4a7ba7d71353a554742fb4997ccaf4f72c2f28ac30bd339","source_identity":"artifact:ticket-autopilot-stale-excluded-final-tree-projection-diagnostic","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | 14: Out of Scope |
| decisions | no matching section identified in the source; complete source retained |
| invariants | 9: Semantic Invariants |
| verification | 13: Verification Strategy |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":6391,"payload_sha256":"193da9cbe36baacda4a7ba7d71353a554742fb4997ccaf4f72c2f28ac30bd339","schema":1,"source_digest":"sha256:193da9cbe36baacda4a7ba7d71353a554742fb4997ccaf4f72c2f28ac30bd339","source_identity":"artifact:ticket-autopilot-stale-excluded-final-tree-projection-diagnostic"} -->
````markdown
# Ticket Autopilot Stale Excluded Final-Tree Projection Reset

## Artifact Graph
- Artifact ID: `artifact:ticket-autopilot-stale-excluded-final-tree-projection-diagnostic`
- Role: `spec`
- Standalone: true

### Children
- [FPR-01 reset stale excluded projections after candidate change](../tickets/ticket-autopilot-stale-excluded-final-tree-projection/done/01-reset-stale-excluded-projection-after-candidate-change.md)

## Type
Bug analysis

## Status
Confirmed against `origin/main`; no implementation has been applied.

## Observed Behavior

With final-tree projection enabled, the runner may record an excluded
`final-tree-projection-plan` immediately after `simplify`, before any delivery preparation exists.
If review then fails and implementation produces a new semantic candidate, the old excluded plan
survives into the new artifact generation. The next simplify/projection pass rejects it with:

```text
persisted final-tree projection exclusion is stale
```

The normal reproducer is:

1. implementation and simplify pass for artifact generation 1;
2. the pre-quality projection check records an excluded plan;
3. review fails and returns the ticket to implementation;
4. a changed implementation candidate advances `artifact_generation` to 2;
5. stale delivery preparation reset runs;
6. implementation and simplify pass again;
7. the generation-2 projection check encounters the generation-1 exclusion and fails.

This does not depend on an abnormal operator sequence. It can occur during the intended
review-fail → implement retry cycle.

## Expected Behavior

When semantic candidate identity changes, stale final-tree projection planning state is archived and
cleared together with every other candidate-bound delivery-preparation receipt. The next simplify may
record a fresh projection plan for the new artifact generation. Equal-candidate replay remains a
no-op, and contradictory or malformed persisted state still fails closed.

## Root Cause

`Kernel.reset_stale_delivery_preparation()` treats `delivery.prepared` as the existence guard for the
entire stale-preparation set. It returns immediately when `prepared` is absent, even though
`STALE_DELIVERY_PREPARATION_STEPS` also contains:

- `final-tree-projection-plan`;
- `final-tree-projection-observation`;
- PR-body, provider, and result receipts.

An excluded pre-quality projection plan is validly persisted before delivery preparation, so the
guard incorrectly assumes an ordering that the projection lifecycle does not guarantee. The stale
plan is never moved to `preparation-history` and never removed.

## Evidence

On `origin/main`:

- `record_final_tree_projection()` explicitly accepts an enabled, excluded plan while the ticket is
  active at review with `implement` and `simplify` validated;
- `STALE_DELIVERY_PREPARATION_STEPS` includes both projection plan and observation;
- `reset_stale_delivery_preparation()` reads `delivery.prepared` and returns `False` immediately when
  it is absent;
- reset callers run during candidate drift and finalizer preparation, so the missing behavior belongs
  in the canonical reset rather than in a one-off caller workaround.

## Semantic Invariants

- Every delivery/projection receipt bound to an old semantic CandidateRef or artifact generation is
  archived before a new candidate can reuse the delivery state.
- Absence of `delivery.prepared` does not imply absence of other candidate-bound preparation receipts.
- Reset archives the exact stale receipts and records one deterministic event; it does not silently
  delete history.
- A reset against the same semantic candidate is idempotent and preserves current preparation.
- Malformed candidate-bound receipts fail closed rather than being guessed stale.
- Review failure retries continue through implementation and simplify without manual ledger surgery.
- Provider, merge, reconciliation, and completion authority are neither granted nor changed.

## Required Change

Make stale-preparation reset derive candidate identity from the complete persisted preparation set,
including an excluded final-tree projection plan when `prepared` is absent. If the available receipt
is well-formed and stale, archive all present steps from `STALE_DELIVERY_PREPARATION_STEPS`, clear
them, and emit the existing reset audit event with the old/new semantic identities and current
artifact generation.

If multiple candidate-bearing receipts exist, they must agree. Contradictory identities are malformed
state and fail closed. Preserve existing behavior when `prepared` is present and when no candidate-
bound preparation receipt exists.

## Acceptance Outcomes

- The regression sequence simplify → excluded projection → review failure → changed candidate →
  simplify succeeds through stale-state reset and may record a fresh generation-2 exclusion.
- The generation-1 exclusion appears in preparation history and no longer occupies the current plan
  slot.
- Same-candidate replay does not archive or clear the current plan.
- A plan-only malformed or contradictory candidate identity fails before mutation.
- Existing prepared-delivery reset tests remain green.
- Kernel and CLI/finalizer coverage prove the ordinary review retry path, not only a direct unit call.

## Failure Modes and Compatibility

Existing schema-4 ledgers may already contain a plan-only stale exclusion. They must remain readable;
the next canonical reset should repair that state through the normal archived-history transition.
No broad ledger rewrite or synthetic delivery preparation is needed. If an old plan lacks enough
identity to prove staleness, stop with an explicit malformed-state error.

## Verification Strategy

Add a focused kernel regression for plan-only reset and an orchestration regression that exercises the
complete review-failure cycle. Assert event/history contents, generation changes, current projection,
transaction rollback on malformed state, and unchanged behavior for prepared delivery. Run focused
final-tree, kernel, finalizer, and CLI suites, followed by the full Ticket Autopilot regression suite.

## Out of Scope

- Changing final-tree eligibility policy or the meaning of `excluded`.
- Bypassing final-tree projection, review, or quality stages.
- Clearing provider or merge evidence that is not part of the stale-preparation contract.
- Repairing unrelated historical ledgers by direct file edit.

````
