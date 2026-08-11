---
ticket_schema: 1
ticket_id: "TK-06"
execution_mode: AFK
blocked_by:
  - "TK-02"
---

# Write the token-reduction guide

## Artifact Graph

- Artifact ID: `artifact:tk-06-write-token-reduction-guide`
- Role: `ticket`
- Parent: [Autopilot Token Economics](../../specs/autopilot-token-economics-wayfinder.md)

## Type
Task

## What to Build
Operator guidance for running autopilot at lower context cost, quoting measured numbers from
`TK-02` rather than plausible ones.

Cover the practices named in the issue and explain why each works or does not:

- Context reset, and when a fresh session is cheaper than continuing an accumulated one.
- Small-context delegation, including that inline composition is the portable default and
  delegation requires explicit authority.
- Cache-friendly practice: a stable static prefix is reused across turns, so churning it for
  small edits is counterproductive, while injecting large volatile content early is
  expensive.

## Acceptance Criteria
- [ ] Every quantitative statement traces to `TK-02` output or is marked as unmeasured.
- [ ] The guide states which practices are operator behaviour and which are contract
      behaviour.
- [ ] It does not claim a percentage saving, a cost saving, or a cache hit rate that no local
      evidence observed.
- [ ] It records that live per-run totals require the `TK-09` observation.
- [ ] Guidance never suggests weakening verification to save context.

## Frontier
Blocked by `TK-02`. Publishing before measurement would produce plausible but unverified
numbers.

## Step-by-Step Plan
1. Generate current figures from the measurement command.
2. Write each practice with its mechanism and its evidence status.
3. Mark every unmeasured claim explicitly and link the live gate.

## Testing Plan
A documentation check that quoted figures match generated output, so the guide fails rather
than drifts when numbers change.

## Out of Scope
- Measuring live consumption.
- Recommending prose compression as a primary lever.
