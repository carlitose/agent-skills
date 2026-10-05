---
ticket_schema: 1
ticket_id: "SLH-01"
execution_mode: AFK
blocked_by: []
---

# SLH-01 — Short skills-only handoff instead of a full Verification Record

## Artifact Graph
- Artifact ID: `artifact:skills-only-light-handoff-slh-01`
- Role: `ticket`
- Parent: [skills-only-light-handoff.md](../../specs/skills-only-light-handoff.md)

## Parent Spec
[skills-only-light-handoff.md](../../specs/skills-only-light-handoff.md): Target behavior, Invariants.

## What to Build
Define the short handoff note in the skills-only contract, make the full Verification Record and
`explain-pr` opt-in for skills-only, and state it in the injected policy, `execute-ticket`,
`verification-audit`, `explain-pr` and `README.md`.

## Acceptance Criteria
- [ ] The skills-only contract defines the note fields and when a full record is required.
- [ ] The injected policy says skills-only ends with the short note, full record only on the listed triggers.
- [ ] `execute-ticket`, `verification-audit` and `explain-pr` describe the same split.
- [ ] Failed, skipped and not-run checks, exact-head CI and provider readback stay required.
- [ ] Extension tests cover the new text; lint passes.

## Frontier
Ready.

## Step-by-Step Implementation Plan
1. Extension tests first (RED), then policy and skills-only contract (GREEN).
2. Align `execute-ticket`, `verification-audit`, `explain-pr`, `README.md`.
3. Run extension tests, skill-graph tests and lint.

## Testing Plan
`node --test extensions/mandatory-agent-skills.test.ts`; skill-graph unit tests; `npm run lint`; CI.

## Out of Scope
- Verification contract code and schema; Autopilot; historical bundles.
