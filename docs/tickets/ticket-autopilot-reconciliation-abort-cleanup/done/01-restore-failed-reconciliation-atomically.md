---
ticket_schema: 1
ticket_id: "RA-01"
execution_mode: AFK
blocked_by: []
---

# Restore failed reconciliation atomically

## Artifact Graph

- Artifact ID: `artifact:ra-01-restore-failed-reconciliation-atomically`
- Role: `ticket`
- Parent: [reconciliation abort cleanup diagnostic](../../specs/ticket-autopilot-reconciliation-abort-cleanup-diagnostic.md)

## Parent Spec

[Ticket-autopilot reconciliation abort cleanup diagnostic](../../specs/ticket-autopilot-reconciliation-abort-cleanup-diagnostic.md)

## What to Build

Make failed initial and target-refresh reconciliation rebases restore their guarded pre-rebase
state before lifecycle validation. Preserve both the causal conflict and any cleanup failure as
durable, actionable evidence.

## Acceptance Criteria

- [ ] A failed reconciliation rebase always attempts `git rebase --abort` before any
      lifecycle or ticket-source check against the conflicted checkout.
- [ ] The compensating abort is authorized only as cleanup for a rebase that passed its
      existing last-safe-boundary guard; unrelated reconciliation mutations retain their
      immediate guards.
- [ ] A successful abort is followed by readback proving that `rebase-merge` and
      `rebase-apply` are absent and that the expected child branch and old local head were
      restored.
- [ ] Lifecycle and source-mode validation runs against the restored checkout, not the
      temporary conflict state.
- [ ] After successful cleanup, the original rebase error becomes the existing durable
      `stack-reconciliation` gate and does not surface as an uncaught source-disposition or
      content-drift error.
- [ ] An abort command or cleanup-readback failure raises one actionable `GitError` that
      preserves both the original rebase failure and cleanup failure, identifies the
      interrupted worktree, and requires explicit recovery.
- [ ] Initial reconciliation and target-refresh reconciliation share one cleanup contract
      rather than duplicating the failure-prone sequence.
- [ ] Regression tests cover lifecycle failure during a conflicted checkout, successful
      cleanup and replay, abort-command failure, incomplete cleanup readback, and both
      reconciliation paths.
- [ ] Reconciliation, lifecycle, Git-boundary, context-boundary, and full ticket-autopilot
      suites pass.

## Frontier

Ready. The masked-error reproduction, ignored abort result, duplicate code paths, and safe
compensation boundary are pinned in the diagnostic.

## Step-by-Step Implementation Plan

1. Add red regressions that reproduce the skipped abort and ignored abort failure in both
   reconciliation functions.
2. Extract a failed-rebase cleanup helper that aborts first and validates command and Git
   readback results.
3. Recheck branch, head, and lifecycle truth only after successful restoration.
4. Route the causal conflict or combined recovery failure through the existing reconciliation
   gate path, then run targeted and full suites.

## Testing Plan

Use TDD around the reconciliation CLI tests. Record command ordering, boundary ordering,
rebase-state readback, branch and head restoration, error text, and durable gate category.
Exercise both normal and refresh derivation with the same cleanup helper, then run the complete
`ticket-autopilot/tests` suite.

## Out of Scope

- Automatically resolving semantic merge conflicts.
- Broad resets, forced checkouts, or deletion of rebase metadata.
- Weakening pre-rebase lifecycle, source-mode, pause, cancel, or provider guards.
- Changing reconciliation equivalence, verification invalidation, or PR publication rules.
