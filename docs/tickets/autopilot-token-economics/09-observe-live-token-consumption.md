---
ticket_schema: 1
ticket_id: "TK-09"
execution_mode: HITL
blocked_by:
  - "TK-04"
---

# Observe live run token consumption

## Artifact Graph

- Artifact ID: `artifact:tk-09-observe-live-token-consumption`
- Role: `ticket`
- Parent: [Autopilot Token Economics](../../specs/autopilot-token-economics-wayfinder.md)

## Type
Task

## What to Build
One human-run observation of what a real autopilot run consumes, compared against the
worst-case ceiling from `TK-04`, with explicit limitations.

This is a host boundary in the same shape as OI-10. The runner is a Python CLI that never
observes model usage, its ledger budgets `interaction`, `tool-call`, and `wall-time` with no
token axis, and `ticket-autopilot/SKILL.md:34` already reports optional host metrics as
`unavailable` unless configured. Only a user-controlled live session can observe totals, so
this ticket never blocks closing issue #53.

## Acceptance Criteria
- [ ] A user-controlled session runs autopilot on a real ticket and records observed usage.
- [ ] The observation names the host, the ticket, and every condition affecting the total.
- [ ] Observed totals are compared against the `TK-04` ceiling, and any breach is explained.
- [ ] Unobservable quantities are recorded as unavailable rather than estimated.
- [ ] No local or simulated evidence is presented as a live observation.
- [ ] The output recommends whether issue #53 can close and states what remains unobserved.

## Frontier
Blocked by `TK-04` and by human availability. The ceiling must exist first to give the
observation a comparison target.

## Step-by-Step Plan
1. Agree the run scope and the host with the user.
2. Execute the run in a user-controlled session and capture available usage data.
3. Compare against the ceiling and record limitations.
4. Recommend a closure decision for the issue.

## Testing Plan
No automated test. Evidence is the recorded observation with its limitations; a passing local
suite is not proof of live behaviour.

## Out of Scope
- Simulating consumption and reporting it as observed.
- Adding a token axis to ledger budgets or gates.
- Blocking issue closure on this observation.
