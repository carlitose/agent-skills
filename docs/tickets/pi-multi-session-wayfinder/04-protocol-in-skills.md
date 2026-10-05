---
ticket_schema: 1
ticket_id: "PMS-04"
execution_mode: AFK
blocked_by:
  - "PMS-03"
---

# PMS-04 — Write the multi-session protocol into the skills

## Artifact Graph
- Artifact ID: `artifact:pi-multi-session-pms-04`
- Role: `ticket`
- Parent: [pi-multi-session-wayfinder.md](../../specs/pi-multi-session-wayfinder.md)

## Parent Spec
[pi-multi-session-wayfinder.md](../../specs/pi-multi-session-wayfinder.md): Destination, Decisions So Far.

## What to Build
Put the protocol confirmed in PMS-03 into the skills where a session reads it (expected: the
skills-only contract of `execute-ticket`, with a pointer from `wayfinder`), and add the rule: after a
PR is merged or closed, always remove its worktree and local branch, then fast-forward the main
checkout.

## Acceptance Criteria
- [ ] The skills-only contract states the confirmed protocol in a few rules.
- [ ] The worktree-removal rule is stated once and applies to every lane that creates a worktree.
- [ ] The Autopilot static-closure budget test still passes (the margin is small).
- [ ] Affected tests and lint pass.

## Frontier
Done: rules in the skills-only contract, pointer in wayfinder, worktree rule in the injected policy.

## Step-by-Step Implementation Plan
1. Test for the new rule text first (RED), then the skill text (GREEN).
2. Keep wording short; check the context-budget and skill-graph tests.

## Testing Plan
Extension and skill-graph tests, `test_context_budget`, `test_artifact_audit`, `npm run lint`, CI.

## Out of Scope
- Changes to pi-messenger or its pin.
- Any runner, scheduler or Crew automation.
