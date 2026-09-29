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
- Rollback restores from a complete marked backup or removes a prior-absent path; neither an unmarked partial copy nor an ownership name permits deletion.
- Missing marked backup fails closed and retains recovery evidence.
- Failure before the first backup and after partial replacement preserves originals/settings/manifest; unchanged skill directories retain identity.

## Step-by-Step Implementation Plan
1. Reproduce the copied-backup directory rename denial and failed marker publication using disposable native Windows tests.
2. Replace directory-rename publication with verified final copy and a completion marker; make rollback inspect proof.
3. Re-run existing Pi sync and platform suites on Windows/Linux, plus provider CI.
4. Pin the immutable integrated head in the portable bundle; exercise old-pin setup -> repaired update in a disposable real Pi profile before any new live attempt.

## Testing Plan
Focused 180-second check ceiling, two corrections per defect. Retain all mandatory provider checks. Do not alter Windows ACLs, stop active processes, send Telegram messages, or reload Pi. Retain backup and receipts if live update fails.

## Out of Scope
Broader source upgrades, unrelated skill changes, scheduler or runner, credentials and runtime activation.
