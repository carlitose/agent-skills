---
type: source
title: "PSR-02 - Publish a verified backup without renaming its directory"
identity_key: ticket:pi-sync-backup-failure/PSR-02
identity_strength: stable
source_path: docs/tickets/pi-sync-backup-failure/02-publish-complete-copy.md
source_digest: sha256:b3d06cbcfb5a3a83941e61c1b27e1c2ef2c87f602330b244e7c203c43d15d1b0
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-29
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# PSR-02 - Publish a verified backup without renaming its directory

Compiled from `docs/tickets/pi-sync-backup-failure/02-publish-complete-copy.md`. Identity is `ticket:pi-sync-backup-failure/PSR-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-29** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/spec-pi-sync-backup-failure]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[7],"status":"present"},"frontier":{"headings":[],"status":"not-identified"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[6],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-pi-sync-backup-failure-psr-02.md","payload_bytes":2357,"payload_sha256":"b3d06cbcfb5a3a83941e61c1b27e1c2ef2c87f602330b244e7c203c43d15d1b0"}],"payload_bytes":2357,"payload_sha256":"b3d06cbcfb5a3a83941e61c1b27e1c2ef2c87f602330b244e7c203c43d15d1b0","schema":1,"source_digest":"sha256:b3d06cbcfb5a3a83941e61c1b27e1c2ef2c87f602330b244e7c203c43d15d1b0","source_identity":"ticket:pi-sync-backup-failure/PSR-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 6: Testing Plan |
| frontier | no matching section identified in the source; complete source retained |
| exclusions | 7: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2357,"payload_sha256":"b3d06cbcfb5a3a83941e61c1b27e1c2ef2c87f602330b244e7c203c43d15d1b0","schema":1,"source_digest":"sha256:b3d06cbcfb5a3a83941e61c1b27e1c2ef2c87f602330b244e7c203c43d15d1b0","source_identity":"ticket:pi-sync-backup-failure/PSR-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "PSR-02"
execution_mode: AFK
blocked_by: []
---

# PSR-02 - Publish a verified backup without renaming its directory

## Artifact Graph
- Artifact ID: `ticket:pi-sync-backup-failure:02`
- Role: `ticket`
- Parent: [spec](../../specs/pi-sync-backup-failure.md)

## Parent Spec
[Preserve owned skills when backup fails](../../specs/pi-sync-backup-failure.md)

## What to Build
On the already-integrated PSR-01 archive head 19aa93f8c06fa11d2ff322272490f7d7748ce739, repair the second Windows WinError 5: renaming backup-staging/ticket-autopilot to backup/skills/ticket-autopilot was denied before touching any live skill. Original 34 skill digests, settings, and ownership manifest are unchanged. Keep this a narrow backport without unrelated newer skill revisions.

## Acceptance Criteria
- Verified copy reaches its final backup path without renaming a directory; only a durable completion marker publishes it.
- Rollback verifies the digest marker, restores by copying the complete backup without a directory rename, and checks the restored digest; only a prior-absent path may be removed without a backup. An unmarked partial copy or an ownership name never permits deletion.
- Missing marked backup fails closed and retains recovery evidence.
- Failure before the first backup and after partial replacement preserves originals/settings/manifest; unchanged skill directories retain identity.

## Step-by-Step Implementation Plan
1. Reproduce the copied-backup directory rename denial and failed marker publication using disposable native Windows tests.
2. Replace directory-rename publication with verified final copy and a completion marker; restore from the marked copy without a directory rename.
3. Re-run existing Pi sync and platform suites on Windows/Linux, plus provider CI.
4. Pin the immutable integrated head in the portable bundle; exercise old-pin setup -> repaired update in a disposable real Pi profile before any new live attempt.

## Testing Plan
Focused 180-second check ceiling, two corrections per defect. Retain all mandatory provider checks. Do not alter Windows ACLs, stop active processes, send Telegram messages, or reload Pi. Retain backup and receipts if live update fails.

## Out of Scope
Broader source upgrades, unrelated skill changes, scheduler or runner, credentials and runtime activation.

```
