---
type: source
title: "Extract one final-tree workflow boundary from the large dispatchers"
identity_key: ticket:autopilot-practical-reliability/APM-06
identity_strength: stable
source_path: docs/tickets/autopilot-practical-reliability/done/06-final-tree-boundary.md
source_digest: sha256:16f6c76bbed37b850aec433e7f93a348d9a14dfda59df1f22b484de161e21617
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-07
created_provenance: git-commit
disposition_changed: 2026-09-09
disposition_changed_provenance: git-rename
run_id: apm-local-recovery-23257eb8
---

# Extract one final-tree workflow boundary from the large dispatchers

Compiled from `docs/tickets/autopilot-practical-reliability/done/06-final-tree-boundary.md`. Identity is `ticket:autopilot-practical-reliability/APM-06`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-07** via `git-commit`
- Disposition changed: **2026-09-09** via `git-rename`

## Graph

- Parent source: [[sources/artifact-autopilot-practical-reliability]]
- Blocked by: [[sources/ticket-autopilot-practical-reliability-apm-04]] — `ticket:autopilot-practical-reliability/APM-04`
- Blocked by: [[sources/ticket-autopilot-practical-reliability-apm-05]] — `ticket:autopilot-practical-reliability/APM-05`

## Run

Completed under autopilot run `apm-local-recovery-23257eb8`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-practical-reliability-apm-06.md","payload_bytes":3381,"payload_sha256":"16f6c76bbed37b850aec433e7f93a348d9a14dfda59df1f22b484de161e21617"}],"payload_bytes":3381,"payload_sha256":"16f6c76bbed37b850aec433e7f93a348d9a14dfda59df1f22b484de161e21617","schema":1,"source_digest":"sha256:16f6c76bbed37b850aec433e7f93a348d9a14dfda59df1f22b484de161e21617","source_identity":"ticket:autopilot-practical-reliability/APM-06","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3381,"payload_sha256":"16f6c76bbed37b850aec433e7f93a348d9a14dfda59df1f22b484de161e21617","schema":1,"source_digest":"sha256:16f6c76bbed37b850aec433e7f93a348d9a14dfda59df1f22b484de161e21617","source_identity":"ticket:autopilot-practical-reliability/APM-06"} -->
```markdown
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

```
