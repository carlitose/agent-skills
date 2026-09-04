---
ticket_schema: 1
ticket_id: "WGC-02"
execution_mode: AFK
blocked_by:
  - "WGC-01"
---

# Apply an exact guarded cleanup plan

## Artifact Graph

- Artifact ID: `artifact:ticket-ticket-autopilot-orphan-worktree-garbage-collection-wgc-02`
- Role: `ticket`
- Parent: [Ticket Autopilot orphan-worktree garbage collection](../../specs/ticket-autopilot-orphan-worktree-garbage-collection.md)

## Parent Spec

[Ticket Autopilot orphan-worktree garbage collection](../../specs/ticket-autopilot-orphan-worktree-garbage-collection.md)

## What to Build

Implement the exact-plan application slice from the parent specification. `worktree-gc-apply` must accept only a validated plan and exact digest with explicit actor/evidence, lock and revalidate the complete eligible set before deletion, persist intent first, remove without force, read back absence, preserve all durable evidence, and resume idempotently after interruption.

## Acceptance Criteria

- [ ] Application rejects malformed or unknown plan, intent, entry-receipt, and completion-receipt fields before interpreting any path.
- [ ] A missing or mismatched expected plan digest, changed worktree inventory, busy run lock, changed ledger/manifest/head/branch/cleanliness/reference state, or newly protected entry removes zero worktrees.
- [ ] All eligible run locks are acquired in deterministic order and every entry passes a complete second preflight before the first removal.
- [ ] An exact actor/evidence-bound intent is durably persisted before deletion; actor/evidence grants no provider, merge, publication, Pi-sync, branch-deletion, or reload authority.
- [ ] Each eligible worktree is removed with ordinary `git worktree remove`, never `--force`, and both filesystem and Git-registration absence are read back.
- [ ] The owner ledger records cleanup while ownership manifests, ledgers, artifacts, candidates, branches, remotes, provider state, and protected worktrees remain intact.
- [ ] Interruption after any applied entry preserves exact receipts; replay verifies prior effects, continues only unchanged remaining entries, and is idempotent.
- [ ] Any post-intent contradiction stops before another removal and reports the exact recovery boundary without fabricating rollback.

## Frontier

Dependency-blocked by WGC-01.

## Step-by-Step Implementation Plan

1. Define strict intent, per-entry applied receipt, and completion receipt contracts bound to the exact plan digest and ordered eligible set.
2. Add repository-level GC locking and deterministic acquisition of all owner run locks.
3. Recompute the plan and require exact safety-input equivalence, then run all-entry preflight before writing intent.
4. Remove entries one at a time without force, read back absence, record ledger cleanup, and atomically persist exact receipts.
5. Implement replay that validates already-applied effects and resumes only unchanged pending entries; stop on every contradiction.
6. Expose `worktree-gc-apply`, document authority exclusions and recovery behavior, and add causal stale-plan/interruption/idempotence tests.

## Testing Plan

- Unit tests for strict receipt schemas, canonical digests, state transitions, and replay contradictions.
- Integration tests proving stale-plan all-or-none preflight, no-force removal, preserved branches/remotes/evidence, and exact ledger cleanup recording.
- Fault-injection tests at intent, removal, readback, ledger-save, entry-receipt, and completion-receipt boundaries.
- Full Ticket Autopilot suite, CLI tests, compile checks, `git diff --check`, and artifact graph audit.

## Out of Scope

- Planning or adopting ownership beyond WGC-01.
- Provider queries or mutations, branch deletion, `git worktree prune`, broad filesystem deletion, Pi synchronization, or reload.
- Removing any protected or unmanaged path.
