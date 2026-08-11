---
ticket_schema: 1
ticket_id: "TK-05"
execution_mode: AFK
blocked_by: []
---

# Document autopilot dependencies

## Artifact Graph

- Artifact ID: `artifact:tk-05-document-autopilot-dependencies`
- Role: `ticket`
- Parent: [Autopilot Token Economics](../../../specs/autopilot-token-economics-wayfinder.md)

## Type
Task

## What to Build
A README section documenting what an autopilot run depends on, so a reader can see the cost
and the coupling before starting a run.

`README.md` already documents Python 3, Git, and the provider CLI under
`## Requirements and command surface`. The missing part is the skill-composition closure:
`ticket-autopilot` composes `execute-ticket`, which composes `code-simplification`,
`code-review`, `qa-test-plan`, and `verification-audit`, with `explain-pr` used by
finalization, plus the loaded references `ticket-envelope-v1`, `delivery-pr-body-v1`,
`merge-critical-path-v1`, and `verification-record`.

## Acceptance Criteria
- [ ] Every skill and reference loaded during a run is listed with its role in the run.
- [ ] The list distinguishes skills the scheduler composes from leaves composed inside
      `execute-ticket`.
- [ ] Existing prerequisite documentation is extended, not duplicated.
- [ ] A test or check fails if the documented closure drifts from the actual composition.

## Frontier
Ready. No dependency and no decision remains.

## Step-by-Step Plan
1. Derive the closure from the current contracts.
2. Add the README section next to the existing requirements material.
3. Add a drift check tying the documented list to the real composition.

## Testing Plan
A static check comparing documented dependencies against the composition declared in the
skills, so the section cannot silently rot.

## Out of Scope
- Publishing token figures, which belongs to `TK-06`.
- Changing the composition itself.
