---
ticket_schema: 1
ticket_id: "PMS-03"
execution_mode: HITL
blocked_by:
  - "PMS-01"
  - "PMS-02"
---

# PMS-03 — Confirm the multi-session coordination protocol

## Artifact Graph
- Artifact ID: `artifact:pi-multi-session-pms-03`
- Role: `ticket`
- Parent: [pi-multi-session-wayfinder.md](../../specs/pi-multi-session-wayfinder.md)

## Parent Spec
[pi-multi-session-wayfinder.md](../../specs/pi-multi-session-wayfinder.md): Not Yet Specified (third item).

## What to Build
Use [grilling](../../../grilling/SKILL.md) with the human to confirm the protocol, one question at a
time, in plain Italian with concrete examples, starting from the PMS-01 and PMS-02 findings. Decide:
the claim mechanism; who updates the shared map and when; the merge order and conflict handling
when two PRs touch the same files; the message conventions (claim, done, blocked, merged); how a
session picks the next ready ticket. Expected output: a decision spec
`docs/specs/pi-multi-session-protocol.md` created through `to-spec`, linked from the map.

## Acceptance Criteria
- [ ] Every decision above is confirmed by the human, not assumed.
- [ ] The decision spec states the protocol in a few rules a session can follow.
- [ ] The map records the decisions and drops the resolved unknowns.

## Frontier
Done: decisions confirmed and recorded in [pi-multi-session-protocol.md](../../specs/pi-multi-session-protocol.md).

## Step-by-Step Implementation Plan
1. Summarize PMS-01/PMS-02 findings in a few lines.
2. Grill one decision at a time and record each answer.
3. Write the decision spec and update the map.

## Testing Plan
Artifact-graph audit and lint on the changed docs.

## Out of Scope
- Writing the protocol into the skills (PMS-04).
