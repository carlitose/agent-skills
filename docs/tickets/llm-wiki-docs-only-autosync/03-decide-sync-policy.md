---
ticket_schema: 1
ticket_id: "WS-03"
execution_mode: HITL
blocked_by:
  - "WS-02"
---

# Decide wiki sync scope, identity, delivery, and failure policy

## Artifact Graph
- Artifact ID: `artifact:ws-03-decide-sync-policy`
- Role: `ticket`
- Parent: [llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## Parent Spec
[llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## What to Build
A confirmed decision spec that turns "the wiki is docs-only" into an executable contract.
Invoke canonical [grilling](../../../grilling/SKILL.md) using the `WS-01` evidence and
`WS-02` prototype before recording the decision through `to-spec`.

## Acceptance Criteria
- [ ] The human confirms the exact eligible paths and the treatment of purpose, schema,
      audit, raw sources, assets, binding JSON, and mixed candidates.
- [ ] The decision fixes discovery, tracked classification, partial/multiple/broken states,
      and external wiki ownership.
- [ ] It selects the versioned docs-only request/profile shape and a fresh owning identity
      for post-integration tracked sync.
- [ ] It fixes trigger timing, normalized results, retry ownership, concurrency control,
      and whether sync failure affects only sync or the enclosing run summary.
- [ ] It preserves exact-head merge authorization and names the migration impact on
      docs-only v1.

## Frontier
Blocked by `WS-02` and then by explicit human confirmation. `WS-04` cannot start from an
unconfirmed interview transcript.

## Step-by-Step Implementation Plan
1. Present the research and prototype evidence through `grilling`, one decision at a time.
2. Record the confirmed policy with `to-spec`, including rejected alternatives and rollout.
3. Link the decision reciprocally from this ticket and the parent wayfinder.

## Testing Plan
Validate that every row in the discovery/tracking matrix has exactly one outcome and every
tracked mutation has an owner, CandidateRef, claim ceiling, delivery path, and retry state.

## Out of Scope
- Implementing the selected design.
- Treating silence, AFK mode, or provider access as merge authorization.
