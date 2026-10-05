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
