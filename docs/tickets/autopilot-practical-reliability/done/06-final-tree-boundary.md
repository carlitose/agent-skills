---
ticket_schema: 1
ticket_id: "APM-06"
execution_mode: AFK
blocked_by:
  - "APM-04"
  - "APM-05"
---

# Extract one final-tree workflow boundary from the large dispatchers

## Artifact Graph
- Artifact ID: `artifact:autopilot-practical-reliability-apm-06`
- Role: `ticket`
- Parent: [Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md)

## Parent Spec
[Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md) — S6 — One Final-Tree Vertical Boundary.

## What to Build
Reduce the amount of unrelated CLI and ledger code needed to follow final-tree projection, final-quality retry, candidate invalidation, and replay. Extract one vertical workflow boundary using the existing projection/transaction owners, rather than horizontally rewriting all event handlers or introducing a generic event framework.

## Acceptance Criteria
- [ ] Final-tree event handling has a cohesive explicit interface outside the large CLI dispatcher; corresponding replay-validation organization is scoped to the same family where extraction is needed.
- [ ] Public CLI inputs, event names/order, serialized schema, candidate generation, authority boundaries, and valid replay behavior are unchanged.
- [ ] Tests cover projection/application, same-candidate quality retry, changed-candidate invalidation including stale excluded plans, interruption/replay, and forged transitions through the public orchestration path.
- [ ] Non-final-tree operations continue through their existing path; no wiki/bootstrap/merge subsystem rewrite is included.
- [ ] Negative replay validation and independent expected-state assertions remain; a shared helper alone is not treated as independent correctness evidence.
- [ ] Before/after function size, dependencies, and a concrete final-tree change-navigation example demonstrate reduced coordination rather than just moving the same dispatcher wholesale.

## Frontier
Dependency-blocked by APM-04, APM-05.

Execute inline. AFK does not authorize subagents; explicit user request is required. This ticket does not authorize provider publication or merge.

## Step-by-Step Implementation Plan
1. Freeze baseline behavior and map only the final-tree branches in _process_events and _validate_event_transition using codebase-design vocabulary.
2. Extract the smallest end-to-end final-tree orchestration boundary and narrow validation helpers, reusing final_tree_projection.py and final_tree_transaction.py.
3. Retain strict event/replay checks and add public-path regression coverage for retry, invalidation, and recovery plus a non-final-tree control case.
4. Run the unified full checks and compare navigation/function-dependency measurements. Defer the next extraction unless this slice shows concrete leverage.

## Testing Plan
- Real local Git plus kernel/CLI/ledger integration for the final-tree lifecycle and interrupted replay; forged-state negative cases remain mandatory.
- Existing full runtime regression suite and non-final-tree control cases; no live provider behavior is claimed.

These are planned checks, not evidence that implementation or verification has occurred.

## Out of Scope
- Whole-engine rewrite, all-event migration, or a new event bus/plugin registry.
- Schema changes, legacy migrations, security-policy changes, or removing replay checks to simplify the code.
