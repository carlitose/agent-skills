---
ticket_schema: 1
ticket_id: "WGC-01"
execution_mode: AFK
blocked_by: []
---

# Register ownership and plan orphan cleanup

## Artifact Graph

- Artifact ID: `artifact:ticket-ticket-autopilot-orphan-worktree-garbage-collection-wgc-01`
- Role: `ticket`
- Parent: [Ticket Autopilot orphan-worktree garbage collection](../../specs/ticket-autopilot-orphan-worktree-garbage-collection.md)

## Parent Spec

[Ticket Autopilot orphan-worktree garbage collection](../../specs/ticket-autopilot-orphan-worktree-garbage-collection.md)

## What to Build

Implement the ownership and provider-free planning slice from the parent specification. New Ticket Autopilot run worktrees must receive immutable `worktree-owner-v1` manifests. Legacy worktrees may be adopted only through the exact ledger-digest, actor/evidence-bound public command. Add a deterministic `worktree-gc-plan` command that enumerates only valid manifests and classifies each owned worktree as eligible or protected without contacting a provider or mutating any worktree or ledger.

## Acceptance Criteria

- [ ] New isolated run creation persists and reads back an exact content-addressed ownership manifest, or compensates safely and fails visibly.
- [ ] `worktree-owner-adopt` rejects unknown fields, invalid ledger integrity, wrong digests, active locks, duplicate claims, symlinks, path aliases, unexpected Git registration, path-shape mismatch, base mismatch, remote/repository mismatch, and arbitrary unmanaged directories.
- [ ] `worktree-gc-plan` writes a canonical digest-addressed plan under the bound Git common directory and is byte-identical for unchanged safety inputs.
- [ ] Planning makes no provider call and never mutates a worktree, branch, ledger, candidate, or provider record.
- [ ] Running, waiting, failed, aborted, locked, dirty, interrupted, unretained, cross-referenced, malformed, open-PR/wiki, incomplete-Pi-sync, primary, invocation, explicit-protected, and unmanaged worktrees are not eligible.
- [ ] A completely terminal, retained, clean, unlocked, runner-unreferenced owned worktree is eligible with all observed evidence and deterministic reason ordering.
- [ ] A WDT-01-shaped completed ledger with `wiki-sync.delivery.status = pr-open` and incomplete Pi-sync intent is protected.

## Frontier

Ready. This is the first executable slice after the exact integrated WDT-01 code and MRA wiki head.

## Step-by-Step Implementation Plan

1. Define strict canonical schemas and digest helpers for immutable ownership manifests and cleanup plans in a focused Ticket Autopilot module.
2. Bind new-run worktree creation to manifest persistence and exact readback, with narrow compensation for a clean detached base if setup fails.
3. Add exact legacy adoption using the existing integrity-protected ledger, managed path, Git common-directory, local remote, Git-dir, base, and lock contracts.
4. Inventory `git worktree list --porcelain -z`, validated manifests, owner ledgers, active cross-references, Git operation state, tracked-wiki delivery, and Pi-sync state without provider access.
5. Classify entries fail-closed, persist the digest-addressed plan atomically, and expose the adoption and plan commands through the public CLI.
6. Add focused unit, CLI, integration, adversarial path, no-provider, and deterministic-output tests plus documentation.

## Testing Plan

- Unit tests for schemas, canonical digests, identity/path normalization, reason ordering, and local terminal-state classifiers.
- Integration fixtures covering valid creation/adoption and every protected-state class in the specification.
- Command-runner assertions that planning invokes no provider adapter and performs no Git mutation.
- Focused Ticket Autopilot tests, compile checks, `git diff --check`, and artifact graph audit.

## Out of Scope

- Removing any worktree.
- Force removal, metadata pruning, branch deletion, provider observation or mutation, Pi synchronization, or reload.
- Automatically adopting a legacy path.
