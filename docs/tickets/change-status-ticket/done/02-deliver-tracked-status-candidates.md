---
ticket_schema: 1
ticket_id: "CST-02"
execution_mode: AFK
blocked_by:
  - "CST-01"
---

# Deliver tracked status candidates through terminal proof

## Artifact Graph

- Artifact ID: `artifact:cst-02-tracked-status-delivery`
- Role: `ticket`
- Parent: [Change Status Ticket](../../specs/change-status-ticket.md)

## Parent Spec

[Change Status Ticket](../../specs/change-status-ticket.md)

## What to Build

Extend the repository lifecycle transaction with the tracked pending-source vertical slice. Create a clean detached administrative worktree at the exact target SHA, apply the receipted source move and deterministic inbound-link repoints, freeze content-complete Git identities under an exact allowlist, and deliver one provider-neutral administrative commit through exact PR readback, separate repository merge authority, fresh terminal proof, terminal source readback, and repository projection.

## Acceptance Criteria

- [ ] The admin worktree starts with a clean index/worktree and never reads target-run staged or unstaged state into its candidate.
- [ ] The allowed change is exactly the old ticket path, new disposition path, and deterministic inbound-link repoints; symlinks, path escapes, submodules, conflicts, unrelated paths, or unexpected allowed-path content fail.
- [ ] Candidate evidence binds parent tree/SHA, candidate tree, raw statuses, modes, old/new blobs, and file bytes; path-only, patch-ID, message, or final-tree similarity is insufficient.
- [ ] Lifecycle intent and applied source receipt precede candidate freeze; commit intent precedes commit; exact parent/tree/diff readback precedes provider dispatch.
- [ ] Push/PR intent precedes dispatch, exact base/head/provider readback follows it, and an armed unknown dispatch reconciles read-only without redispatch.
- [ ] Provider mutation is limited to the exact administrative PR; no target issue, existing PR, or ignored source is published or closed.
- [ ] Merge consumes only separate canonical repository authority bound to the exact PR head and fresh checks/policies; external merge observation grants no mutation authority.
- [ ] Provider `MERGED` alone is not integration; fresh terminal-branch reachability of the exact delivered head is required.
- [ ] Repository terminal receipt and source path/digest are appended only after terminal proof; replay appends no second commit, PR, merge, or projection.
- [ ] Target-branch advance before preparation rebuilds from fresh target; drift after provider intent gates for exact reconciliation.
- [ ] Dirty target checkout/index, commit/provider/merge crash points, stale provider head/base, and missing terminal reachability have causal disposable tests.
- [ ] No real ticket disposition or live provider mutation is required for verification.

## Frontier

Dependency-blocked by CST-01. Once its repository journal and tracked handoff are integrated, this ticket is AFK with fake providers and disposable bare remotes.

## Step-by-Step Implementation Plan

1. Add admin-worktree creation, clean-state checks, lifecycle source application, and deterministic repoints.
2. Freeze the exact candidate contract and runner-authored single administrative commit.
3. Add provider intent/readback and ambiguity-safe replay using existing provider-neutral adapters.
4. Reuse separate repository merge authority and terminal integration proof without widening either contract.
5. Add terminal source readback, repository projection, crash recovery, and disposable bare-remote forward tests.

## Testing Plan

Use dirty target checkouts, clean detached admin worktrees, fake providers, and bare remotes. Vary file content/modes/paths, target advances, dispatch crashes, PR drift, checks/policies, external merge, and terminal reachability. Assert exact single-shot effects and stable gates.

## Out of Scope

- Active/gated/waiting state projection or repository mutation barrier.
- Public skill/routing changes.
- Ignored-source publication, target-ticket implementation, issue operations, wiki, Pi-sync, or cleanup.
- Treating merge authority or terminal proof as disposition authority.
