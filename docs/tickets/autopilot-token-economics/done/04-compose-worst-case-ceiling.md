---
ticket_schema: 1
ticket_id: "TK-04"
execution_mode: AFK
blocked_by:
  - "TK-02"
  - "TK-03"
---

# Compose the worst-case per-turn ceiling

## Artifact Graph

- Artifact ID: `artifact:tk-04-compose-worst-case-ceiling`
- Role: `ticket`
- Parent: [Autopilot Token Economics](../../specs/autopilot-token-economics-wayfinder.md)

## Type
Task

## What to Build
Compose the measured static prefix from `TK-02` with the declared intake bounds from `TK-03`
into a single worst-case per-turn context ceiling, and guard it against regression.

Neither input alone yields a per-turn number: the static prefix ignores volatile content, and
a declared bound is a contract rather than a measurement. Their composition is the strongest
statement this repository can prove without host telemetry.

## Acceptance Criteria
- [ ] The ceiling is computed from both inputs and reported in the frozen unit.
- [ ] The report names every assumption that makes it a worst case rather than an estimate.
- [ ] A regression check fails when the ceiling grows without a deliberate raise.
- [ ] Raising the ceiling is an explicit, reviewable action distinct from breaching it.
- [ ] The check adds no token axis to ledger budgets, gates, or merge authorization.
- [ ] Output states that the ceiling is an upper bound and not observed consumption.

## Frontier
Blocked by `TK-02` and `TK-03`.

## Step-by-Step Plan
1. Define the composition rule and its worst-case assumptions.
2. Extend the measurement output with the composed ceiling.
3. Add the regression check and the deliberate-raise procedure.
4. Document how a legitimate contract growth is distinguished from accidental bloat.

## Testing Plan
Fixtures for a stable ceiling, an accidental breach, and a deliberate raise. Assert the check
cannot gate a run, a delivery, or a merge.

## Out of Scope
- Live measurement.
- Making the ceiling a scheduling or delivery precondition.
