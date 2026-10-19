---
type: source
title: "PBD-01 — Leave bytecode caches out of the skill digest"
identity_key: ticket:pi-sync-bytecode-drift/PBD-01
identity_strength: stable
source_path: docs/tickets/pi-sync-bytecode-drift/done/01-ignore-bytecode-caches.md
source_digest: sha256:0d3ec6f505ef0647cec8e0bacd04e576d59e0e68a2c4c23405e4821174b57a96
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-30
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# PBD-01 — Leave bytecode caches out of the skill digest

Compiled from `docs/tickets/pi-sync-bytecode-drift/done/01-ignore-bytecode-caches.md`. Identity is `ticket:pi-sync-bytecode-drift/PBD-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-30** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/spec-pi-sync-bytecode-drift]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-pi-sync-bytecode-drift-pbd-01.md","payload_bytes":1642,"payload_sha256":"0d3ec6f505ef0647cec8e0bacd04e576d59e0e68a2c4c23405e4821174b57a96"}],"payload_bytes":1642,"payload_sha256":"0d3ec6f505ef0647cec8e0bacd04e576d59e0e68a2c4c23405e4821174b57a96","schema":1,"source_digest":"sha256:0d3ec6f505ef0647cec8e0bacd04e576d59e0e68a2c4c23405e4821174b57a96","source_identity":"ticket:pi-sync-bytecode-drift/PBD-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1642,"payload_sha256":"0d3ec6f505ef0647cec8e0bacd04e576d59e0e68a2c4c23405e4821174b57a96","schema":1,"source_digest":"sha256:0d3ec6f505ef0647cec8e0bacd04e576d59e0e68a2c4c23405e4821174b57a96","source_identity":"ticket:pi-sync-bytecode-drift/PBD-01"} -->
```markdown
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

```
