---
ticket_schema: 1
ticket_id: "JCI-01"
execution_mode: AFK
blocked_by: []
---

# JCI-01 — Give fallback judges run-scoped unique identities

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-judge-identity-01`
- Role: `ticket`
- Parent: [ticket-driver-judge-identity.md](../../specs/ticket-driver-judge-identity.md)

## Parent Spec
[ticket-driver-judge-identity.md](../../specs/ticket-driver-judge-identity.md)

## What to Build
Allocate the next unused judge name across `Cascade` instances of one run, accounting for existing receipts and partially created session directories. Keep the fresh leaf behavior and fail-closed cascade unchanged.

## Acceptance Criteria
- [ ] Initial semantic gate and another after directed retry can both invoke fallback judges in one run without reusing a name or overwriting existing receipts, with accurate `judge-1`, `judge-2` etc sessions.
- [ ] Existing partially-created session cannot be reused and a second judge may still gate legitimately; Jev question/threshold/answer policy unchanged.
- [ ] Synthetic RED/GREEN, c1b/c2/c3 regression and mandatory quick profile observed, c3b-r4 permanently recorded as a failed attempt.

## Frontier
Ready: observed collision, deterministic reproduction available with fake Jev uncertainty and directed blocker retry. Human benchmark mandate and local fix authorization remain within the c3/c4 goal; no live attempt in this ticket.

## Step-by-Step Implementation Plan
1. Add a fake-leaf causal test forcing uncertainty in two semantic gate passes and verifying distinct judge sessions.
2. Allocate judge identities by existing run receipts and session paths instead of instance-local counter alone; preserve evidence and question behavior.
3. Run RED/GREEN, regression and quick profile; review, deliver/sync exact-head under established repo authority, and separately bind future benchmark starts.

## Testing Plan
Use fake Pi/Jev and temporary repos; test both repeated semantic gate and stale session directory, then full focused suites and selected local profile. No hosted model/Jev.

## Out of Scope
Changing bench38 seed/tests, old receipts, model/Jev policy, customer code, Autopilot runner or forcing uncertain decisions to yes.
