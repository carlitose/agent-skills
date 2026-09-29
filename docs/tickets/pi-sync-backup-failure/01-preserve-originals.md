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
