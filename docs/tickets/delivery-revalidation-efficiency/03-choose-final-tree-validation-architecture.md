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
