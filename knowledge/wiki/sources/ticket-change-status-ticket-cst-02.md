---
type: source
title: "Deliver tracked status candidates through terminal proof"
identity_key: ticket:change-status-ticket/CST-02
identity_strength: stable
source_path: docs/tickets/change-status-ticket/done/02-deliver-tracked-status-candidates.md
source_digest: sha256:0f90dee3442309b1a3628a996ae045b3aa66abb0bcadbf2969595764e42490de
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-01
created_provenance: git-commit
disposition_changed: 2026-09-01
disposition_changed_provenance: git-rename
run_id: change-status-ticket-production-20260831
---

# Deliver tracked status candidates through terminal proof

Compiled from `docs/tickets/change-status-ticket/done/02-deliver-tracked-status-candidates.md`. Identity is `ticket:change-status-ticket/CST-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-01** via `git-commit`
- Disposition changed: **2026-09-01** via `git-rename`

## Graph

- Parent source: [[sources/artifact-change-status-ticket]]
- Blocked by: [[sources/ticket-change-status-ticket-cst-01]] — `ticket:change-status-ticket/CST-01`

## Run

Completed under autopilot run `change-status-ticket-production-20260831`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-change-status-ticket-cst-02.md","payload_bytes":4118,"payload_sha256":"0f90dee3442309b1a3628a996ae045b3aa66abb0bcadbf2969595764e42490de"}],"payload_bytes":4118,"payload_sha256":"0f90dee3442309b1a3628a996ae045b3aa66abb0bcadbf2969595764e42490de","schema":1,"source_digest":"sha256:0f90dee3442309b1a3628a996ae045b3aa66abb0bcadbf2969595764e42490de","source_identity":"ticket:change-status-ticket/CST-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4118,"payload_sha256":"0f90dee3442309b1a3628a996ae045b3aa66abb0bcadbf2969595764e42490de","schema":1,"source_digest":"sha256:0f90dee3442309b1a3628a996ae045b3aa66abb0bcadbf2969595764e42490de","source_identity":"ticket:change-status-ticket/CST-02"} -->
```markdown
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

```
