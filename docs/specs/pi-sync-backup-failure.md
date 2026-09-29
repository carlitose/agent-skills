# Preserve owned skills when backup fails

## Artifact Graph
- Artifact ID: `spec:pi-sync-backup-failure`
- Role: `spec`
- Standalone: true
- Child: [PSR-01](../tickets/pi-sync-backup-failure/01-preserve-originals.md)

## Incident and target
The authorized personal updater used the archive pinned to `d82b9d17257f44ab4358a428ff3d2fb4c38d52c2`. Windows denied `os.replace` of the first live skill directory. `_rollback` then deleted every name in the prewritten ownership inventory without requiring a backup or prior-absence marker. All 34 owned skills disappeared. Exact backups were verified against the unchanged ownership manifest and restored; no updater retry is permitted before a regression-tested correction.

This is an intentionally narrow backport on the same dependency baseline, not an upgrade to unrelated newer skill changes. Source scope: `ticket-autopilot/scripts/autopilot/pi_sync.py`, its causal tests, and this spec/ticket. Inline skills-only; no scheduler, runner or subagents. Unrelated dirty files in the primary checkout are excluded by a separate worktree.

## Required behavior
- Backup failure before the first or a later mutation preserves every original and unrelated skill and settings byte.
- The ownership inventory is not evidence that a mutation occurred. Rollback may remove a destination only when a complete published backup or explicit prior-absence marker exists.
- Stage a full copy of a live directory and verify both its digest and the unchanged source before atomically publishing a backup. A partial copy is not a usable backup. Do not rename the original live directory (Windows may deny that operation while reading it).
- Reuse owned directories whose contents already match the target. Preserve drift rejection, owner/source identity, replacement authorization, settings reconciliation and receipt semantics.
- Never change ACLs, stop other processes or discard user drift. A subsequent failure remains visible and retains recovery artifacts if restoration fails.

## Verification
Test-first permission failures on first/later backup; partial-copy failure; Windows live-root-rename refusal; unchanged directory identity; existing install/readback/crash/recovery suite. Test in native Windows and Linux. Publish only this backport; use its immutable archive in the personal updater after provider integration evidence. Actual local update and runtime activation remain separate checks. Initial test ceiling: 180 seconds targeted, 2 corrections per defect; mandatory provider checks remain authoritative.
