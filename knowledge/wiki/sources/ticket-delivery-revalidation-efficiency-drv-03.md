---
type: source
title: "Choose the final-tree validation architecture"
identity_key: ticket:delivery-revalidation-efficiency/DRV-03
identity_strength: stable
source_path: docs/tickets/delivery-revalidation-efficiency/done/03-choose-final-tree-validation-architecture.md
source_digest: sha256:690716918fe5f8c0a703cac7231eba54f9381e89e890f06d7c9ab25beb2ee969
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-01
created_provenance: git-commit
disposition_changed: 2026-09-02
disposition_changed_provenance: git-rename
run_id: delivery-revalidation-final-tree-decision-20260902
---

# Choose the final-tree validation architecture

Compiled from `docs/tickets/delivery-revalidation-efficiency/done/03-choose-final-tree-validation-architecture.md`. Identity is `ticket:delivery-revalidation-efficiency/DRV-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-01** via `git-commit`
- Disposition changed: **2026-09-02** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-revalidation-efficiency-wayfinder]]
- Blocked by: [[sources/ticket-delivery-revalidation-efficiency-drv-01]] — `ticket:delivery-revalidation-efficiency/DRV-01`
- Blocked by: [[sources/ticket-delivery-revalidation-efficiency-drv-02]] — `ticket:delivery-revalidation-efficiency/DRV-02`

## Run

Completed under autopilot run `delivery-revalidation-final-tree-decision-20260902`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-revalidation-efficiency-drv-03.md","payload_bytes":2679,"payload_sha256":"690716918fe5f8c0a703cac7231eba54f9381e89e890f06d7c9ab25beb2ee969"}],"payload_bytes":2679,"payload_sha256":"690716918fe5f8c0a703cac7231eba54f9381e89e890f06d7c9ab25beb2ee969","schema":1,"source_digest":"sha256:690716918fe5f8c0a703cac7231eba54f9381e89e890f06d7c9ab25beb2ee969","source_identity":"ticket:delivery-revalidation-efficiency/DRV-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2679,"payload_sha256":"690716918fe5f8c0a703cac7231eba54f9381e89e890f06d7c9ab25beb2ee969","schema":1,"source_digest":"sha256:690716918fe5f8c0a703cac7231eba54f9381e89e890f06d7c9ab25beb2ee969","source_identity":"ticket:delivery-revalidation-efficiency/DRV-03"} -->
```markdown
---
ticket_schema: 1
ticket_id: "DRV-03"
execution_mode: HITL
blocked_by:
  - "DRV-01"
  - "DRV-02"
---

# Choose the final-tree validation architecture

## Artifact Graph
- Artifact ID: `ticket:delivery-revalidation-efficiency:DRV-03`
- Role: `ticket`
- Parent: [Delivery revalidation efficiency wayfinder](../../specs/delivery-revalidation-efficiency-wayfinder.md)

## Parent Spec
[Delivery revalidation efficiency wayfinder](../../specs/delivery-revalidation-efficiency-wayfinder.md)

## What to Build
Use `grilling` with a human decision owner to choose completion projection before final quality, proof-carrying deterministic projection, a bounded hybrid, or explicit retention of the current full revalidation cycle.

The decision must consume DRV-01 and DRV-02 evidence, preserve every semantic invariant in the parent map, and define the exact next `to-spec` inputs. Silence, AFK mode, benchmark speed, or implementation convenience cannot select the architecture.

## Acceptance Criteria
- [ ] The human explicitly confirms one option or retention of current behavior.
- [ ] The decision records exact projection scope, final-tree identity, lifecycle ordering, evidence carry-forward, proof/test-selection contract, failure/recovery semantics, historical compatibility, and rollout/rollback.
- [ ] Security and under-testing counterarguments are answered with DRV-01/DRV-02 evidence.
- [ ] Separate completion, verification, merge, reconciliation, provider, terminal, wiki, and Pi authorities remain explicit.
- [ ] A focused decision or architecture spec is produced through `to-spec` only after confirmation.
- [ ] Production tickets are emitted only from that confirmed spec.

## Frontier
HITL. Blocked by DRV-01 and DRV-02, then by explicit human confirmation through `grilling`.

## Step-by-Step Implementation Plan
1. Present the evidence and strongest objections for every option.
2. Ask one decision question at a time and record confirmed constraints.
3. Test the selected option against every invariant and must-revalidate case.
4. Record the decision, rejected alternatives, consequences, and rollback.
5. Route the confirmed result to `to-spec`; do not implement inline.

## Testing Plan
- Validate that every decision field has explicit human confirmation and an evidence reference.
- Confirm no unresolved high-impact question is silently defaulted.
- Check Artifact Graph reciprocity and links in the resulting decision spec.
- Confirm no production candidate, PR, or authority mutation occurs in this ticket.

## Out of Scope
- Making the decision autonomously.
- Implementing or merging the optimization.
- Weakening exact final-tree or terminal proof.

```
