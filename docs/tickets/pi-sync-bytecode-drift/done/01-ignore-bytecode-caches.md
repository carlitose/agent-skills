---
ticket_schema: 1
ticket_id: "PBD-01"
execution_mode: AFK
blocked_by: []
---

# PBD-01 — Leave bytecode caches out of the skill digest

## Artifact Graph
- Artifact ID: `ticket:pi-sync-bytecode-drift:01`
- Role: `ticket`
- Parent: [pi-sync-bytecode-drift.md](../../specs/pi-sync-bytecode-drift.md)

## Parent Spec
[pi-sync-bytecode-drift.md](../../specs/pi-sync-bytecode-drift.md)

## What to Build
`_tree_digest` in `ticket-autopilot/scripts/autopilot/pi_sync.py` skips `__pycache__`
directories, so Python's bytecode caches in a used skill are not drift. Everything else about
the drift check, ownership and rollback stays the same.

## Acceptance Criteria
- [x] With caches in a changed and in an unchanged installed skill, the next head installs;
  before the fix it fails with `previously owned skill drifted: alpha`.
- [x] A changed file next to a cache is still refused as drift.
- [x] The existing `test_pi_sync` and `test_pi_sync_windows` suites pass.

## Outcome
2026-09-30. `test_bytecode_caches_of_used_skills_are_not_drift` fails before the fix and passes
after it, with the `test_pi_sync` and `test_pi_sync_windows` suites.

## Frontier
Closed. The installed skills adopt it with the next pin advance in pi-personal-config.

## Step-by-Step Implementation Plan
1. RED test in `test_pi_sync.py`.
2. Prune `__pycache__` in `_tree_digest`.
3. Run the two pi_sync suites.

## Testing Plan
`python -B -m unittest tests.test_pi_sync tests.test_pi_sync_windows` from `ticket-autopilot`.

## Out of Scope
- Other bytecode locations (`PYTHONPYCACHEPREFIX`, legacy `.pyc` next to sources).
- Advancing the pin in pi-personal-config.
