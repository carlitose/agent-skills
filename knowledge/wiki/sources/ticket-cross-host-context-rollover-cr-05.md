---
type: source
title: "Map supported Claude Code compaction controls"
identity_key: ticket:cross-host-context-rollover/CR-05
identity_strength: stable
source_path: docs/tickets/cross-host-context-rollover/done/05-map-supported-compaction-controls.md
source_digest: sha256:978fdc4af3ca62c04b5ddb45a17c524870705d3a3fe9bcc6f3a044474ee7338d
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-28
created_provenance: git-commit
disposition_changed: 2026-08-29
disposition_changed_provenance: git-rename
run_id: cr-autocompact-removal-20260829
---

# Map supported Claude Code compaction controls

Compiled from `docs/tickets/cross-host-context-rollover/done/05-map-supported-compaction-controls.md`. Identity is `ticket:cross-host-context-rollover/CR-05`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-28** via `git-commit`
- Disposition changed: **2026-08-29** via `git-rename`

## Graph

- Parent source: [[sources/artifact-cross-host-context-rollover-wayfinder]]
- Child source: [[sources/artifact-cross-host-context-compaction-controls]]
- Blocked by: [[sources/ticket-cross-host-context-rollover-cr-03]] — `ticket:cross-host-context-rollover/CR-03`

## Run

Completed under autopilot run `cr-autocompact-removal-20260829`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[5],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[4],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-cross-host-context-rollover-cr-05.md","payload_bytes":2630,"payload_sha256":"978fdc4af3ca62c04b5ddb45a17c524870705d3a3fe9bcc6f3a044474ee7338d"}],"payload_bytes":2630,"payload_sha256":"978fdc4af3ca62c04b5ddb45a17c524870705d3a3fe9bcc6f3a044474ee7338d","schema":1,"source_digest":"sha256:978fdc4af3ca62c04b5ddb45a17c524870705d3a3fe9bcc6f3a044474ee7338d","source_identity":"ticket:cross-host-context-rollover/CR-05","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 4: What to Build |
| acceptance | 5: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2630,"payload_sha256":"978fdc4af3ca62c04b5ddb45a17c524870705d3a3fe9bcc6f3a044474ee7338d","schema":1,"source_digest":"sha256:978fdc4af3ca62c04b5ddb45a17c524870705d3a3fe9bcc6f3a044474ee7338d","source_identity":"ticket:cross-host-context-rollover/CR-05"} -->
```markdown
---
ticket_schema: 1
ticket_id: "CR-05"
execution_mode: AFK
blocked_by:
  - "CR-03"
---

# Map supported Claude Code compaction controls

## Artifact Graph

- Artifact ID: `artifact:cr-05-map-supported-compaction-controls`
- Role: `ticket`
- Parent: [Cross-host Context Rollover](../../specs/cross-host-context-rollover-wayfinder.md)

### Produces

- [Claude Code compaction control baseline](../../research/cross-host-context-compaction-controls.md)

## Parent Spec

[Cross-host Context Rollover](../../specs/cross-host-context-rollover-wayfinder.md)

## What to Build

Turn the baseline report into version-bound evidence for supported Claude Code compaction
controls. Separate official documentation, local CLI help, and observed runtime effects. Do
not treat `--autocompact` as an eligible solution.

## Acceptance Criteria

- [ ] The report binds exact local versions, sanitized help surfaces, and official-source
      revisions without storing credentials or transcript content.
- [ ] Isolated temporary-configuration probes classify `DISABLE_COMPACT`, blocking
      `PreCompact`, `PostCompact`, and `/compact` as `supported`, `unsupported`, or
      `unobserved`.
- [ ] A help entry alone never becomes runtime evidence, and `--autocompact` remains rejected
      even where a local binary parses it.
- [ ] No probe changes global hooks, shell configuration, Claude settings, or unrelated
      sessions.
- [ ] The report fixes the capability contract that CR-06 consumes: supported prevention,
      observation-only, or visible `no-go` before 150,000 tokens.
- [ ] Unavailable live boundaries stay explicit and do not become passing simulated claims.

## Frontier

Ready. The destination is fixed; only current host capability evidence is missing.

## Step-by-Step Implementation Plan

1. Capture versioned official and local command surfaces with secret-safe evidence.
2. Build isolated fixtures for environment and hook control candidates.
3. Run the smallest authorized probes and classify each observed boundary.
4. Update the baseline report with evidence, limits, and the exact CR-06 contract.

## Testing Plan

Use temporary directories and sanitized fixture inputs. Unit checks validate classification
and prevent help-only promotion. Any real host process probe remains local and must record its
version, configuration isolation, exit behavior, and limitations.

## Out of Scope

- Restoring `--autocompact` under another version gate.
- Editing the rollover prototype; CR-06 owns that change.
- Installing global hooks or changing global Claude configuration.
- Running the HITL live rollover owned by CR-04.

```
