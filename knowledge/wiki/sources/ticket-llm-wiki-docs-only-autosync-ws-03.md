---
type: source
title: "Decide wiki sync scope, identity, delivery, and failure policy"
identity_key: ticket:llm-wiki-docs-only-autosync/WS-03
identity_strength: stable
source_path: docs/tickets/llm-wiki-docs-only-autosync/done/03-decide-sync-policy.md
source_digest: sha256:c2b2539f1f30a16f082f615234b7a2842bd976b098dc558b82e9e20be91141a6
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-28
created_provenance: git-commit
disposition_changed: 2026-08-28
disposition_changed_provenance: git-rename
run_id: f74e8975ae4d49a5
---

# Decide wiki sync scope, identity, delivery, and failure policy

Compiled from `docs/tickets/llm-wiki-docs-only-autosync/done/03-decide-sync-policy.md`. Identity is `ticket:llm-wiki-docs-only-autosync/WS-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-28** via `git-commit`
- Disposition changed: **2026-08-28** via `git-rename`

## Graph

- Parent source: [[sources/artifact-llm-wiki-docs-only-autosync-wayfinder]]
- Blocked by: [[sources/ticket-llm-wiki-docs-only-autosync-ws-02]] — `ticket:llm-wiki-docs-only-autosync/WS-02`

## Run

Completed under autopilot run `f74e8975ae4d49a5`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-docs-only-autosync-ws-03.md","payload_bytes":2196,"payload_sha256":"c2b2539f1f30a16f082f615234b7a2842bd976b098dc558b82e9e20be91141a6"}],"payload_bytes":2196,"payload_sha256":"c2b2539f1f30a16f082f615234b7a2842bd976b098dc558b82e9e20be91141a6","schema":1,"source_digest":"sha256:c2b2539f1f30a16f082f615234b7a2842bd976b098dc558b82e9e20be91141a6","source_identity":"ticket:llm-wiki-docs-only-autosync/WS-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2196,"payload_sha256":"c2b2539f1f30a16f082f615234b7a2842bd976b098dc558b82e9e20be91141a6","schema":1,"source_digest":"sha256:c2b2539f1f30a16f082f615234b7a2842bd976b098dc558b82e9e20be91141a6","source_identity":"ticket:llm-wiki-docs-only-autosync/WS-03"} -->
```markdown
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

```
