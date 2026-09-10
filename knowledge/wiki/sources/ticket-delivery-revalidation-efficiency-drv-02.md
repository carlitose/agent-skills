---
type: source
title: "Prototype projection-proof options"
identity_key: ticket:delivery-revalidation-efficiency/DRV-02
identity_strength: stable
source_path: docs/tickets/delivery-revalidation-efficiency/done/02-prototype-projection-proof-options.md
source_digest: sha256:ff61ff701343ede89ae0c35de845e85d356dc26d4d245efc08b5aa79dc6025a9
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-01
created_provenance: git-commit
disposition_changed: 2026-09-01
disposition_changed_provenance: git-rename
run_id: delivery-revalidation-efficiency-evidence-20260901
---

# Prototype projection-proof options

Compiled from `docs/tickets/delivery-revalidation-efficiency/done/02-prototype-projection-proof-options.md`. Identity is `ticket:delivery-revalidation-efficiency/DRV-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-01** via `git-commit`
- Disposition changed: **2026-09-01** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-revalidation-efficiency-wayfinder]]
- Blocked by: [[sources/ticket-delivery-revalidation-efficiency-drv-01]] — `ticket:delivery-revalidation-efficiency/DRV-01`

## Run

Completed under autopilot run `delivery-revalidation-efficiency-evidence-20260901`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-revalidation-efficiency-drv-02.md","payload_bytes":2862,"payload_sha256":"ff61ff701343ede89ae0c35de845e85d356dc26d4d245efc08b5aa79dc6025a9"}],"payload_bytes":2862,"payload_sha256":"ff61ff701343ede89ae0c35de845e85d356dc26d4d245efc08b5aa79dc6025a9","schema":1,"source_digest":"sha256:ff61ff701343ede89ae0c35de845e85d356dc26d4d245efc08b5aa79dc6025a9","source_identity":"ticket:delivery-revalidation-efficiency/DRV-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2862,"payload_sha256":"ff61ff701343ede89ae0c35de845e85d356dc26d4d245efc08b5aa79dc6025a9","schema":1,"source_digest":"sha256:ff61ff701343ede89ae0c35de845e85d356dc26d4d245efc08b5aa79dc6025a9","source_identity":"ticket:delivery-revalidation-efficiency/DRV-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DRV-02"
execution_mode: AFK
blocked_by:
  - "DRV-01"
---

# Prototype projection-proof options

## Artifact Graph
- Artifact ID: `ticket:delivery-revalidation-efficiency:DRV-02`
- Role: `ticket`
- Parent: [Delivery revalidation efficiency wayfinder](../../specs/delivery-revalidation-efficiency-wayfinder.md)

## Parent Spec
[Delivery revalidation efficiency wayfinder](../../specs/delivery-revalidation-efficiency-wayfinder.md)

## What to Build
Build a throwaway, standard-library-only model comparing three unselected architectures: completion projection before the final quality cycle, proof-carrying deterministic projection after implementation verification, and a bounded hybrid.

The prototype must model exact trees, blobs, modes, ticket bytes, receipts, link repoints, artifact generations, evidence segments, budgets, crash checkpoints, and replay. It must fail closed for arbitrary or ambiguous drift and leave only durable findings in the parent map or its research report.

## Acceptance Criteria
- [ ] All three candidate designs share the same explicit state/effect fixtures.
- [ ] Positive fixtures cover exact tracked move, same-byte/mode ticket, canonical receipt, approved link repoints, and negative extra-diff proof.
- [ ] Negative fixtures cover extra path/blob/mode changes, changed receipt fields, stale CandidateRef, tampered proof, duplicate effects, ignored-source drift, reconciliation drift, provider mutation, and crash ambiguity.
- [ ] Each design reports lifecycle truthfulness, recovery complexity, proof surface, test-selection risk, compatibility impact, command avoidance, and residual full-revalidation cases.
- [ ] Prototype code and state are deleted; only reproducible contract, results, cleanup proof, and limitations persist.
- [ ] No production architecture is selected.

## Frontier
Blocked by DRV-01. Its output unblocks DRV-03.

## Step-by-Step Implementation Plan
1. Derive fixtures and invariants from DRV-01 rather than inventing a parallel lifecycle.
2. Freeze expected outcomes before implementing the model.
3. Run all designs against identical positive, negative, crash, and replay matrices.
4. Measure proof complexity and avoided work without calling providers or mutating real runs.
5. Delete the prototype and fold the labeled results into the durable frontier evidence.

## Testing Plan
- Unit-test every fixture and exact digest transition.
- Use mutation-style negatives to prove one extra effect forces full revalidation.
- Verify deterministic replay and crash recovery for every checkpoint.
- Confirm no prototype files, caches, generated state, or run-ledger drift remains.

## Out of Scope
- Production code or migration.
- Live provider mutation.
- Choosing a design or test threshold.
- General test-impact analysis outside deterministic completion projection.

```
