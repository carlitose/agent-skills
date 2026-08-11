---
ticket_schema: 1
ticket_id: "TK-08"
execution_mode: AFK
blocked_by: []
---

# Record the context-passing boundary

## Artifact Graph

- Artifact ID: `artifact:tk-08-record-context-passing-boundary`
- Role: `ticket`
- Parent: [Autopilot Token Economics](../../../specs/autopilot-token-economics-wayfinder.md)

## Type
Task

## What to Build
Make the context-passing boundary observable so it cannot be reopened by guesswork. The
issue asks whether the main agent should use `handoff` to pass context to subagents; the
evidence says no.

`handoff/SKILL.md:12` already states it is neither scheduler state nor a ticket-autopilot
checkpoint, it writes only to the operating-system temporary directory, and it carries
`disable-model-invocation: true`. Context reaches leaves through the `leaf-result` schema-3
contract of `resume --events`, described in `ticket-autopilot/SKILL.md:48-53`. The work is to
state that split explicitly on both sides and test it.

## Acceptance Criteria
- [ ] The `handoff` boundary names the leaf channel it is not, in addition to the scheduler
      state it already excludes.
- [ ] The autopilot side names the channel that does own leaf context passing.
- [ ] A test asserts `handoff` is not referenced as the leaf or subagent context mechanism.
- [ ] No change is made to `handoff` storage, redaction, or expiry behaviour.
- [ ] No change is made to the `leaf-result` schema or its validation.

## Frontier
Ready. The decision is already evidenced in the parent map; only its observability is missing.

## Step-by-Step Plan
1. Add the explicit boundary statement to the `handoff` contract.
2. Name the owning leaf channel on the autopilot side.
3. Add the regression test for the boundary.

## Testing Plan
A prompt-level test asserting the boundary text on both sides and that no skill routes leaf
context through `handoff`.

## Out of Scope
- Changing `leaf-result` schema, validation, or digest rules.
- Repurposing `handoff` as durable or scheduler state.
- Altering redaction, expiry, or temporary-directory behaviour.
