---
type: source
title: "PSR-01 - Preserve originals when owned-skill backup fails"
identity_key: ticket:pi-sync-backup-failure/PSR-01
identity_strength: stable
source_path: docs/tickets/pi-sync-backup-failure/01-preserve-originals.md
source_digest: sha256:c31458ce07284474ef7ef914960c3053720f3e563561b12707677a2f011ff93a
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-29
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# PSR-01 - Preserve originals when owned-skill backup fails

Compiled from `docs/tickets/pi-sync-backup-failure/01-preserve-originals.md`. Identity is `ticket:pi-sync-backup-failure/PSR-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-29** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/spec-pi-sync-backup-failure]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[7],"status":"present"},"frontier":{"headings":[],"status":"not-identified"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[6],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-pi-sync-backup-failure-psr-01.md","payload_bytes":1565,"payload_sha256":"c31458ce07284474ef7ef914960c3053720f3e563561b12707677a2f011ff93a"}],"payload_bytes":1565,"payload_sha256":"c31458ce07284474ef7ef914960c3053720f3e563561b12707677a2f011ff93a","schema":1,"source_digest":"sha256:c31458ce07284474ef7ef914960c3053720f3e563561b12707677a2f011ff93a","source_identity":"ticket:pi-sync-backup-failure/PSR-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 6: Testing Plan |
| frontier | no matching section identified in the source; complete source retained |
| exclusions | 7: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1565,"payload_sha256":"c31458ce07284474ef7ef914960c3053720f3e563561b12707677a2f011ff93a","schema":1,"source_digest":"sha256:c31458ce07284474ef7ef914960c3053720f3e563561b12707677a2f011ff93a","source_identity":"ticket:pi-sync-backup-failure/PSR-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "PSR-01"
execution_mode: AFK
blocked_by: []
---

# PSR-01 - Preserve originals when owned-skill backup fails

## Artifact Graph
- Artifact ID: `ticket:pi-sync-backup-failure:01`
- Role: `ticket`
- Parent: [spec](../../specs/pi-sync-backup-failure.md)

## Parent Spec
[Preserve owned skills when backup fails](../../specs/pi-sync-backup-failure.md)

## What to Build
Narrow repair of canonical Pi sync backup and rollback on dependency baseline d82b9d17257f44ab4358a428ff3d2fb4c38d52c2. No unrelated dependency upgrade.

## Acceptance Criteria
- First/later backup failures cannot delete unsaved originals.
- Partial copies cannot become rollback sources.
- Identical skill directories are retained, not renamed.
- A verified staged backup exists before any original is removed.
- Existing rollback, adoption, drift, settings and identity checks remain covered.

## Step-by-Step Implementation Plan
1. Reproduce failed-first-backup mechanism in disposable tests.
2. Bind rollback to saved backup or prior-absence proof.
3. Verify staged copies before publishing; retain unchanged directories.
4. Run sync suites, freeze backport and review inline.

## Testing Plan
Native Windows and Linux. 180-second focused command ceiling; two correction attempts per defect. Provider checks cannot be waived. Live scope remains blocked until integration and updated dependency verification.

## Out of Scope
ACL changes, process termination, ownership adoption, scheduler actions, credentials, Telegram sends and unrelated newer skill revisions.

```
