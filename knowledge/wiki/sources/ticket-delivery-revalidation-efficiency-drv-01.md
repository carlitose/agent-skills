---
type: source
title: "Map the completion-to-delivery revalidation flow"
identity_key: ticket:delivery-revalidation-efficiency/DRV-01
identity_strength: stable
source_path: docs/tickets/delivery-revalidation-efficiency/done/01-map-current-flow-and-cost.md
source_digest: sha256:70a3c6993bfd1931f217b8233d8c11fa5c12f2808368de2dacdf8d3f4fb663df
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-01
created_provenance: git-commit
disposition_changed: 2026-09-01
disposition_changed_provenance: git-rename
run_id: delivery-revalidation-efficiency-evidence-20260901
---

# Map the completion-to-delivery revalidation flow

Compiled from `docs/tickets/delivery-revalidation-efficiency/done/01-map-current-flow-and-cost.md`. Identity is `ticket:delivery-revalidation-efficiency/DRV-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-01** via `git-commit`
- Disposition changed: **2026-09-01** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-revalidation-efficiency-wayfinder]]
- Child source: [[sources/artifact-delivery-revalidation-current-flow-and-cost]]

## Run

Completed under autopilot run `delivery-revalidation-efficiency-evidence-20260901`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[5],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[4],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-revalidation-efficiency-drv-01.md","payload_bytes":3045,"payload_sha256":"70a3c6993bfd1931f217b8233d8c11fa5c12f2808368de2dacdf8d3f4fb663df"}],"payload_bytes":3045,"payload_sha256":"70a3c6993bfd1931f217b8233d8c11fa5c12f2808368de2dacdf8d3f4fb663df","schema":1,"source_digest":"sha256:70a3c6993bfd1931f217b8233d8c11fa5c12f2808368de2dacdf8d3f4fb663df","source_identity":"ticket:delivery-revalidation-efficiency/DRV-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 4: What to Build |
| acceptance | 5: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3045,"payload_sha256":"70a3c6993bfd1931f217b8233d8c11fa5c12f2808368de2dacdf8d3f4fb663df","schema":1,"source_digest":"sha256:70a3c6993bfd1931f217b8233d8c11fa5c12f2808368de2dacdf8d3f4fb663df","source_identity":"ticket:delivery-revalidation-efficiency/DRV-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DRV-01"
execution_mode: AFK
blocked_by: []
---

# Map the completion-to-delivery revalidation flow

## Artifact Graph
- Artifact ID: `ticket:delivery-revalidation-efficiency:DRV-01`
- Role: `ticket`
- Parent: [Delivery revalidation efficiency wayfinder](../../specs/delivery-revalidation-efficiency-wayfinder.md)

### Produces
- [Delivery revalidation current-flow and cost report](../../research/delivery-revalidation-current-flow-and-cost.md)

## Parent Spec
[Delivery revalidation efficiency wayfinder](../../specs/delivery-revalidation-efficiency-wayfinder.md)

## What to Build
Complete the current-state and cost investigation seeded in the linked research report. Map the exact call graph, state transitions, effects, CandidateRefs, artifacts, budgets, replay paths, and authorities from verified implementation through completion projection, delivery revalidation, provider mutation, terminal proof, and post-integration handling.

Separate causally necessary final-tree checks from broad checks repeated only because the runner lacks a narrower proof contract. Include tracked, ignored, recovery, reconciliation, and historical-ledger cases without proposing implementation.

## Acceptance Criteria
- [ ] The report cites every owning production module and representative test family.
- [ ] A state/effect table covers normal tracked completion, ignored source, reconciliation, recovery, crash/replay, provider-before/after, and terminal proof.
- [ ] Each effect names path/blob/mode/tree/receipt/link/ledger changes and the evidence it invalidates.
- [ ] At least three completed runs are measured with a reproducible command-count and wall-time method, or unavailable samples are reported as a limitation.
- [ ] Full-revalidation false positives and must-revalidate negatives are explicit.
- [ ] The parent map is updated with durable facts and unresolved proof questions only.
- [ ] No design, test-selection policy, or production change is selected.

## Frontier
Ready. This evidence unblocks DRV-02 and DRV-03.

## Step-by-Step Implementation Plan
1. Trace finalizer, kernel, CLI, ticket-source, recovery, reconciliation, provider, and terminal-integration paths.
2. Build state/effect and evidence-invalidation tables from code and tests.
3. Measure available completed-run duplicate cycles without mutating their ledgers or artifacts.
4. Record must-revalidate counterexamples and candidate deterministic classes.
5. Update the report and fold only stable findings into the wayfinder.

## Testing Plan
- Resolve every repository citation and Artifact Graph edge.
- Run focused kernel, CLI, and ticket-source tests covering cited transitions.
- Recompute cost summaries from raw run artifacts and label missing/non-comparable samples.
- Confirm all inspected run ledgers remain byte-identical.

## Out of Scope
- Implementing a projection proof.
- Choosing among pre-projection, proof-carrying, or hybrid designs.
- Changing verification, merge, completion, reconciliation, wiki, or Pi authority.

```
