---
type: source
title: "Reset stale excluded projection after candidate change"
identity_key: ticket:ticket-autopilot-stale-excluded-final-tree-projection/FPR-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-stale-excluded-final-tree-projection/done/01-reset-stale-excluded-projection-after-candidate-change.md
source_digest: sha256:d663a703a1a89a74d1dc9e065a03107639725cb0f62be953f40fb4f6df91a618
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-05
created_provenance: git-commit
disposition_changed: 2026-09-05
disposition_changed_provenance: git-rename
run_id: fpr01-stale-excluded-projection-20260904
---

# Reset stale excluded projection after candidate change

Compiled from `docs/tickets/ticket-autopilot-stale-excluded-final-tree-projection/done/01-reset-stale-excluded-projection-after-candidate-change.md`. Identity is `ticket:ticket-autopilot-stale-excluded-final-tree-projection/FPR-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-05** via `git-commit`
- Disposition changed: **2026-09-05** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-stale-excluded-final-tree-projection-diagnostic]]

## Run

Completed under autopilot run `fpr01-stale-excluded-projection-20260904`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-stale-excluded-final-tree-projection-fpr-01.md","payload_bytes":4474,"payload_sha256":"d663a703a1a89a74d1dc9e065a03107639725cb0f62be953f40fb4f6df91a618"}],"payload_bytes":4474,"payload_sha256":"d663a703a1a89a74d1dc9e065a03107639725cb0f62be953f40fb4f6df91a618","schema":1,"source_digest":"sha256:d663a703a1a89a74d1dc9e065a03107639725cb0f62be953f40fb4f6df91a618","source_identity":"ticket:ticket-autopilot-stale-excluded-final-tree-projection/FPR-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4474,"payload_sha256":"d663a703a1a89a74d1dc9e065a03107639725cb0f62be953f40fb4f6df91a618","schema":1,"source_digest":"sha256:d663a703a1a89a74d1dc9e065a03107639725cb0f62be953f40fb4f6df91a618","source_identity":"ticket:ticket-autopilot-stale-excluded-final-tree-projection/FPR-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "FPR-01"
execution_mode: AFK
blocked_by: []
---

# Reset stale excluded projection after candidate change

## Artifact Graph
- Artifact ID: `artifact:fpr-01-reset-stale-excluded-projection-after-candidate-change`
- Role: `ticket`
- Parent: [stale excluded final-tree projection diagnostic](../../specs/ticket-autopilot-stale-excluded-final-tree-projection-diagnostic.md)

## Parent Spec
[stale excluded final-tree projection diagnostic](../../specs/ticket-autopilot-stale-excluded-final-tree-projection-diagnostic.md)

## What to Build
Fix the canonical stale-delivery-preparation reset so candidate-bound final-tree projection state is archived and cleared even when `delivery.prepared` has never been recorded. The implementation must support the normal cycle: simplify, persist an enabled excluded projection for generation 1, fail review, adopt a changed implementation candidate at generation 2, simplify again, and record a fresh projection instead of raising `persisted final-tree projection exclusion is stale`.

Derive the old semantic identity from the complete candidate-bearing preparation set rather than using `prepared` as the sole existence guard. Preserve the current prepared-delivery path. If multiple receipts supply identity they must agree; malformed or contradictory state fails before mutation. Archive every present `STALE_DELIVERY_PREPARATION_STEPS` receipt and retain the existing deterministic reset event/history semantics.

## Acceptance Criteria
- [ ] A plan-only excluded final-tree projection is recognized as candidate-bound preparation when `delivery.prepared` is absent.
- [ ] When its semantic candidate differs, reset archives the exact old projection, clears the current slot, records old/new CandidateRefs and current artifact generation, and returns `True`.
- [ ] The end-to-end regression simplify → excluded plan → review fail → changed implementation candidate → simplify proceeds without stale-exclusion failure and can persist a generation-2 plan.
- [ ] Same-candidate reset is idempotent, returns `False`, and preserves the current plan.
- [ ] Prepared-delivery reset behavior and all existing stale preparation steps remain unchanged.
- [ ] Multiple candidate-bearing receipts with contradictory identities and plan-only malformed identities fail closed with zero partial mutation.
- [ ] Existing schema-4 ledgers need no bulk rewrite; a valid stale plan-only state converges through the normal reset transition.
- [ ] Kernel, finalizer/orchestration, CLI, and focused final-tree tests prove the causal path, followed by the full Ticket Autopilot suite.

## Frontier
Ready and AFK. The diagnosis and expected state transition are complete; no product, provider, or human decision is required.

## Step-by-Step Implementation Plan
1. Inventory every entry in `STALE_DELIVERY_PREPARATION_STEPS` and identify which receipts carry semantic candidate identity. Checkpoint: plan-only exclusion and prepared delivery are both represented.
2. Refactor `reset_stale_delivery_preparation()` to select and validate one consistent old semantic identity without treating `prepared` absence as an empty state.
3. Reuse the existing receipt archive, clearing, and event path for every stale candidate-bearing shape. Checkpoint: history contains the exact projection receipt and current state no longer does.
4. Add direct unit tests for plan-only stale, same-candidate, malformed, contradictory, and existing prepared cases.
5. Add the full review-failure retry regression through the ordinary runner/finalizer boundary and run focused plus full suites.

## Testing Plan
Automated causal tests must first reproduce the exact stale error on the old behavior, then pass after the fix. Assert artifact-generation changes, CandidateRefs, preparation history, current delivery keys, event payload, transaction rollback, and successful generation-2 simplify/projection. Run the focused final-tree projection, kernel, finalizer, and CLI tests and the full Ticket Autopilot suite.

No live provider mutation is needed. Existing provider, merge, reconciliation, and completion behavior is regression scope only and must not be claimed from local tests beyond the covered boundary.

## Out of Scope
- Changing final-tree eligibility or disabling projection.
- Adding synthetic `delivery.prepared` records.
- Directly editing active ledgers.
- Merge, reconciliation, wiki, Pi, or historical gate-reason changes.

```
