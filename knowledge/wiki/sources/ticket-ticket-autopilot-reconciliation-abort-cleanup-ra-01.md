---
type: source
title: "Restore failed reconciliation atomically"
identity_key: ticket:ticket-autopilot-reconciliation-abort-cleanup/RA-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-reconciliation-abort-cleanup/done/01-restore-failed-reconciliation-atomically.md
source_digest: sha256:f3a75ff3bbfd6c00747014beceb31c3b56662106baa426affc4c3db44e03ec67
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-29
created_provenance: git-commit
disposition_changed: 2026-08-29
disposition_changed_provenance: git-rename
run_id: ra01-abort-cleanup-20260829
---

# Restore failed reconciliation atomically

Compiled from `docs/tickets/ticket-autopilot-reconciliation-abort-cleanup/done/01-restore-failed-reconciliation-atomically.md`. Identity is `ticket:ticket-autopilot-reconciliation-abort-cleanup/RA-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-29** via `git-commit`
- Disposition changed: **2026-08-29** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-reconciliation-abort-cleanup-diagnostic]]

## Run

Completed under autopilot run `ra01-abort-cleanup-20260829`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-reconciliation-abort-cleanup-ra-01.md","payload_bytes":3621,"payload_sha256":"f3a75ff3bbfd6c00747014beceb31c3b56662106baa426affc4c3db44e03ec67"}],"payload_bytes":3621,"payload_sha256":"f3a75ff3bbfd6c00747014beceb31c3b56662106baa426affc4c3db44e03ec67","schema":1,"source_digest":"sha256:f3a75ff3bbfd6c00747014beceb31c3b56662106baa426affc4c3db44e03ec67","source_identity":"ticket:ticket-autopilot-reconciliation-abort-cleanup/RA-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3621,"payload_sha256":"f3a75ff3bbfd6c00747014beceb31c3b56662106baa426affc4c3db44e03ec67","schema":1,"source_digest":"sha256:f3a75ff3bbfd6c00747014beceb31c3b56662106baa426affc4c3db44e03ec67","source_identity":"ticket:ticket-autopilot-reconciliation-abort-cleanup/RA-01"} -->
```markdown
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

```
