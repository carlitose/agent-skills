---
type: source
title: "Adopt redacted temporary session handoff"
identity_key: ticket:mattpocock-skills-adoption/U-06
identity_strength: stable
source_path: docs/tickets/mattpocock-skills-adoption/done/06-adopt-session-handoff.md
source_digest: sha256:3f8f952e1dd4581a005a94e009e8fd1e431e71eb700df1a3dbc1bba42302a9c2
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-08
created_provenance: git-commit
disposition_changed: 2026-08-09
disposition_changed_provenance: git-rename
run_id: b9aeeb5529b642fd
---

# Adopt redacted temporary session handoff

Compiled from `docs/tickets/mattpocock-skills-adoption/done/06-adopt-session-handoff.md`. Identity is `ticket:mattpocock-skills-adoption/U-06`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-08** via `git-commit`
- Disposition changed: **2026-08-09** via `git-rename`

## Run

Completed under autopilot run `b9aeeb5529b642fd`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-mattpocock-skills-adoption-u-06.md","payload_bytes":1550,"payload_sha256":"3f8f952e1dd4581a005a94e009e8fd1e431e71eb700df1a3dbc1bba42302a9c2"}],"payload_bytes":1550,"payload_sha256":"3f8f952e1dd4581a005a94e009e8fd1e431e71eb700df1a3dbc1bba42302a9c2","schema":1,"source_digest":"sha256:3f8f952e1dd4581a005a94e009e8fd1e431e71eb700df1a3dbc1bba42302a9c2","source_identity":"ticket:mattpocock-skills-adoption/U-06","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1550,"payload_sha256":"3f8f952e1dd4581a005a94e009e8fd1e431e71eb700df1a3dbc1bba42302a9c2","schema":1,"source_digest":"sha256:3f8f952e1dd4581a005a94e009e8fd1e431e71eb700df1a3dbc1bba42302a9c2","source_identity":"ticket:mattpocock-skills-adoption/U-06"} -->
```markdown
---
ticket_schema: 1
ticket_id: "U-06"
execution_mode: AFK
blocked_by: []
---

# Adopt redacted temporary session handoff

## Parent Spec
[Open GitHub Issues Remediation](../../specs/open-github-issues-wayfinder.md)

## Adoption Source
[OI-07 approved parity selection](../../research/mattpocock-skills-parity.md#oi-07-approved-adoption-selection)

## What to Build
Add a session-handoff skill that writes a small pointer-based, redacted artifact in the operating-system temporary directory with explicit expiry/deletion guidance. It must not become scheduler state or a Git-tracked project artifact.

## Acceptance Criteria
- [ ] The output contract records purpose, durable pointers, remaining work, limitations, and redacted context.
- [ ] Sensitive values and unnecessary transcript content are excluded.
- [ ] Storage is temporary, untracked, and accompanied by cleanup/expiry guidance.
- [ ] Tests validate output shape and redaction without mutating runner state.

## Frontier
Ready; no dependency or human decision remains.

## Step-by-Step Implementation Plan
1. Define the minimal handoff schema and redaction boundary.
2. Add the skill and Codex metadata with an OS-temp-only workflow.
3. Test deterministic shape, pointer preservation, and cleanup guidance.

## Testing Plan
Use temporary-directory fixtures and static metadata/link checks; assert the repository and scheduler ledger remain unchanged.

## Out of Scope
- Ticket-autopilot checkpoints, resumability, or ledger ownership.
- Persisting session transcripts or secrets in Git.

```
