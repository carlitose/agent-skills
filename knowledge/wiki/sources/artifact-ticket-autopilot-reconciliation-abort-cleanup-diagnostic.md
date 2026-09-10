---
type: source
title: "Ticket-Autopilot Reconciliation Abort Cleanup"
identity_key: artifact:ticket-autopilot-reconciliation-abort-cleanup-diagnostic
identity_strength: stable
source_path: docs/specs/ticket-autopilot-reconciliation-abort-cleanup-diagnostic.md
source_digest: sha256:9d6d61c43b01bea70d44cfb86b4df4147889b25341170c0dc9f5727bc2298a76
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-08-29
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Ticket-Autopilot Reconciliation Abort Cleanup

Compiled from `docs/specs/ticket-autopilot-reconciliation-abort-cleanup-diagnostic.md`. Identity is `artifact:ticket-autopilot-reconciliation-abort-cleanup-diagnostic`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-29** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-ticket-autopilot-reconciliation-abort-cleanup-ra-01]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-ticket-autopilot-reconciliation-abort-cleanup-diagnostic.md","payload_bytes":6324,"payload_sha256":"9d6d61c43b01bea70d44cfb86b4df4147889b25341170c0dc9f5727bc2298a76"}],"payload_bytes":6324,"payload_sha256":"9d6d61c43b01bea70d44cfb86b4df4147889b25341170c0dc9f5727bc2298a76","schema":1,"source_digest":"sha256:9d6d61c43b01bea70d44cfb86b4df4147889b25341170c0dc9f5727bc2298a76","source_identity":"artifact:ticket-autopilot-reconciliation-abort-cleanup-diagnostic","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":6324,"payload_sha256":"9d6d61c43b01bea70d44cfb86b4df4147889b25341170c0dc9f5727bc2298a76","schema":1,"source_digest":"sha256:9d6d61c43b01bea70d44cfb86b4df4147889b25341170c0dc9f5727bc2298a76","source_identity":"artifact:ticket-autopilot-reconciliation-abort-cleanup-diagnostic"} -->
```markdown
# Ticket-Autopilot Reconciliation Abort Cleanup

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-reconciliation-abort-cleanup-diagnostic`
- Role: `spec`
- Standalone: true

### Children

- [RA-01 restore failed reconciliation atomically](../tickets/ticket-autopilot-reconciliation-abort-cleanup/done/01-restore-failed-reconciliation-atomically.md)

## Type

Diagnostic spec

## Status

Fixed by RA-01; full-suite verification is bound to the ticket run.

## Diagnosis Report - lens: compensating Git mutation

### Root cause

Both `_derive_reconciliation_candidate()` and
`_derive_reconciliation_refresh_candidate()` guard `git:reconcile*-abort` after a rebase has
already failed but before they execute `git rebase --abort`.

That ordering is invalid for a compensating operation. A conflicted rebase is expected to
leave the checkout and index in a temporary state that differs from the frozen ticket source.
The lifecycle guard observes that temporary conflict, raises before cleanup, and prevents the
abort that would have restored the frozen state. The lifecycle error then masks the causal Git
conflict and the worktree remains mid-rebase.

There is a second failure in the same cleanup path: when the abort command is reached, its
return code is ignored. An abort failure therefore leaves the worktree interrupted while the
runner reports only the original rebase error.

### Evidence

- The normal reconciliation path runs the sequence `guard(reconcile-rebase)`, failed rebase,
  `guard(reconcile-abort)`, then `git rebase --abort`.
- The target-refresh path duplicates the same ordering with
  `reconcile-refresh-rebase` and `reconcile-refresh-abort`.
- A deterministic command-runner reproduction makes the abort boundary raise the same
  lifecycle error produced by ticket-source conflict. The observed exception is
  `LifecycleError: ticket '02' content differs from managed snapshot`; the only recorded
  command is the failed rebase and `abort_executed` is false.
- A second reproduction lets the guard pass and returns exit code 1 from
  `git rebase --abort`. The runner still raises only `GitError: content conflict`, proving
  that cleanup failure is discarded.
- The pre-rebase boundary already validates administrative and ticket-source truth at the
  last safe point before the mutation. The later abort guard does not protect an independent
  forward mutation; it blocks restoration of that previously validated state.

### User-visible failure

A semantic stack reconciliation can fail with a misleading source-disposition or content-drift
error instead of the original rebase conflict. The next resume then finds `rebase-merge` or
`rebase-apply` and requires explicit recovery. The operator cannot safely continue through the
normal audited flow even though the runner itself created the interrupted state.

### Feedback loop built

The regression needs a failed reconciliation rebase followed by a lifecycle guard that would
reject the conflicted checkout. It must prove that cleanup is attempted before any post-failure
source check, that a successful abort restores the original branch and head and removes both
rebase state directories, and that the causal conflict becomes a durable
`stack-reconciliation` gate rather than an uncaught lifecycle drift.

A second case must force `git rebase --abort` itself to fail and prove that the emitted error
preserves both failures, identifies the interrupted worktree, and gives explicit recovery
guidance. Run the same contract against initial reconciliation and target refresh.

### Fix location and approach

Extract one narrow failed-rebase cleanup helper used by both reconciliation functions. The
helper must execute `git rebase --abort` immediately because it is compensation for the
already-guarded rebase, validate the abort exit code, and read back the absence of rebase state.
After successful cleanup, re-run the lifecycle/source boundary against the restored checkout
and verify that the child branch and old local head were recovered.

If cleanup succeeds, raise the original rebase error so the existing reconciliation handler
opens the causal `stack-reconciliation` gate. If cleanup fails or readback proves incomplete,
raise a combined `GitError` that retains the original conflict, reports the cleanup failure,
names the worktree, and requires explicit recovery. Never claim that the worktree is clean.

### Alternatives ruled out

- **Keep the pre-abort lifecycle guard.** Rejected because the temporary state it rejects is
  the exact state that `git rebase --abort` is designed to repair.
- **Remove all mutation boundaries around reconciliation.** Rejected because the pre-rebase
  guard is the correct last-safe-boundary authorization and remains necessary.
- **Ignore the abort result and rely on the next resume.** Rejected because it loses causal
  evidence and turns a locally recoverable failure into an opaque interrupted-run failure.
- **Automatically reset the worktree.** Rejected because a broad reset is destructive and
  does not preserve Git's rebase recovery semantics.
- **Treat the temporary conflict as a source-mode drift gate.** Rejected because the source
  classification did not drift; the runner's guarded mutation temporarily changed the index.

### Confidence: high

The reproduction follows the exact failing branch, command recording proves why cleanup is
skipped, the ignored return code is directly observable, and both affected functions duplicate
the same defective pattern.

## Fix Verification

RA-01 replaces both duplicated failure branches with one compensating cleanup helper. A failed
rebase now runs `git rebase --abort` before the post-failure lifecycle boundary, validates the
abort exit code, proves both rebase-state directories are absent, and reads back the original
branch and head. Only then does it validate lifecycle/source truth and surface the causal rebase
error through the existing reconciliation gate.

If the abort command or cleanup readback fails, the emitted `GitError` retains the original
conflict, identifies the worktree and cleanup failure, and requires explicit recovery. Four
causal regressions were red before the implementation and pass afterward; all 67 CLI tests and
the complete 475-test ticket-autopilot suite pass on the implementation candidate.

```
