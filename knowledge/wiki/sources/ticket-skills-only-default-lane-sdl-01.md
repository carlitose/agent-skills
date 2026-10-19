---
type: source
title: "SDL-01 — Default skills-only lane and direct lane for small changes"
identity_key: ticket:skills-only-default-lane/SDL-01
identity_strength: stable
source_path: docs/tickets/skills-only-default-lane/01-default-and-direct-lane.md
source_digest: sha256:a48fb248000f9a09afd83e79b47369e69842da1d0d042464d1393a5250618436
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# SDL-01 — Default skills-only lane and direct lane for small changes

Compiled from `docs/tickets/skills-only-default-lane/01-default-and-direct-lane.md`. Identity is `ticket:skills-only-default-lane/SDL-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-skills-only-default-lane]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-skills-only-default-lane-sdl-01.md","payload_bytes":1656,"payload_sha256":"a48fb248000f9a09afd83e79b47369e69842da1d0d042464d1393a5250618436"}],"payload_bytes":1656,"payload_sha256":"a48fb248000f9a09afd83e79b47369e69842da1d0d042464d1393a5250618436","schema":1,"source_digest":"sha256:a48fb248000f9a09afd83e79b47369e69842da1d0d042464d1393a5250618436","source_identity":"ticket:skills-only-default-lane/SDL-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1656,"payload_sha256":"a48fb248000f9a09afd83e79b47369e69842da1d0d042464d1393a5250618436","schema":1,"source_digest":"sha256:a48fb248000f9a09afd83e79b47369e69842da1d0d042464d1393a5250618436","source_identity":"ticket:skills-only-default-lane/SDL-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SDL-01"
execution_mode: AFK
blocked_by: []
---

# SDL-01 — Default skills-only lane and direct lane for small changes

## Artifact Graph
- Artifact ID: `artifact:skills-only-default-lane-sdl-01`
- Role: `ticket`
- Parent: [skills-only-default-lane.md](../../specs/skills-only-default-lane.md)

## Parent Spec
[skills-only-default-lane.md](../../specs/skills-only-default-lane.md): Target behavior, Invariants.

## What to Build
Make skills-only the default delivery lane, add the direct lane for small changes, and keep
Autopilot only on explicit request, in the injected policy, `/agent-skills-flow`, `ask-skills`,
the skills-only reference, `execute-ticket`, `to-tickets` and `README.md`.

## Acceptance Criteria
- [ ] The injected policy names skills-only as the default and Autopilot as explicit-request only.
- [ ] The injected policy defines the direct lane: eligibility, required checks, escalation.
- [ ] `ask-skills` routing and `README.md` describe the same three lanes.
- [ ] `/agent-skills-flow` reports the default lane without selecting or changing it.
- [ ] Extension tests cover default, direct lane and explicit Autopilot; lint passes.

## Frontier
Ready.

## Step-by-Step Implementation Plan
1. Update extension tests first (RED), then the policy text and flow message (GREEN).
2. Update `ask-skills`, the skills-only reference, `execute-ticket`, `to-tickets`, `README.md`.
3. Run extension tests and lint.

## Testing Plan
`node --test extensions/mandatory-agent-skills.test.ts`; `npm run lint`; CI.

## Out of Scope
- Verification Record simplification; Autopilot internals; historical docs and wiki.

```
