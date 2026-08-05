---
ticket_schema: 1
ticket_id: "04"
execution_mode: AFK
blocked_by: []
---

# Support Git-ignored ticket sources

## Parent Spec

[ticket-autopilot-ignored-ticket-sources.md](../../specs/ticket-autopilot-ignored-ticket-sources.md)

## What to Build

Resolve [GitHub issue #21](https://github.com/carlitose/agent-skills/issues/21) end to end.
Allow canonical tickets under a fully Git-ignored in-repository folder to drive a run
through an immutable managed snapshot, while preserving the existing tracked-folder path
and preventing ignored planning files from entering the implementation PR.

## Acceptance Criteria

- [ ] Run initialization classifies ticket input as `tracked` or `ignored`; paths outside
      the repository, mixed tracked/ignored sets, and untracked non-ignored inputs fail
      before worktree creation.
- [ ] Every consumed ticket is parsed canonically and atomically snapshotted under the
      managed run directory with normalized envelope, body, relative path, content digest,
      source mode, and a manifest digest.
- [ ] Resume and scheduling consume the immutable snapshot rather than mutable caller
      files, while `CandidateRef` retains the exact snapshot-derived ticket digest.
- [ ] Tracked mode preserves existing isolated-worktree move, completion summary, and Git
      staging behavior.
- [ ] Ignored mode does not require the ticket inside the isolated worktree and never stages
      the ignored source or completion summary.
- [ ] Ignored finalization atomically moves the exact digest-matched caller source to its
      ignored `done/` path and writes a matching completion summary beside it.
- [ ] Intent/applied receipts make crashes before or after the external move replay-safe;
      changed, missing, duplicate, or contradictory source/destination content gates instead
      of overwriting data.
- [ ] Snapshot and finalization path checks reject symlink escapes and any mutation outside
      the accepted ticket folder.
- [ ] Plan, status, and final reports expose source mode, manifest digest, completion effect,
      and any source-drift gate.
- [ ] Automated tests prove tracked parity, ignored success, ignored files absent from the
      PR commit, mixed/untracked rejection, drift detection, containment, and crash resume.

## Frontier

Ready. This ticket is independent of delivery-body and merge-path work and unblocks the
documentation join in ticket `07`.

## Step-by-Step Implementation Plan

1. Introduce a strict source classifier using Git tracked-at-base and positive ignore
   evidence; preserve the existing selected-base comparison for tracked mode.
2. Define and atomically persist the versioned normalized snapshot manifest before creating
   the isolated worktree; bind the ledger to its digest and source mode.
3. Make kernel initialization and resume use the managed snapshot while retaining original
   bounded source paths only for finalization effects.
4. Split finalization into tracked and ignored adapters under one idempotent effect contract.
5. Add ignored-source intent/applied receipts and reconciliation rules for every move/write
   crash window and contradictory state.
6. Project source state through reports, document explicit compatibility behavior, and add
   causal unit/integration tests.

## Testing Plan

Run ticket contract, Git operations, finalizer, kernel, ledger replay, CLI, and forward-test
suites. Use isolated repositories with nested ignore rules, spaces, symlinks, changed ignore
rules, source mutation, pre-existing destinations, injected write/move failures, and dirty
unrelated caller files. Assert exact commits and Git status in both source modes.

## Out of Scope

- Ticket folders outside the repository.
- Accepting arbitrary untracked input through a force flag.
- Changing the canonical Ticket Envelope or adding a second parser.
- Automatically changing `.gitignore` or tracking ignored planning files.
