---
type: source
title: "Apply an exact guarded cleanup plan"
identity_key: ticket:ticket-autopilot-orphan-worktree-garbage-collection/WGC-02
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-orphan-worktree-garbage-collection/done/02-apply-exact-guarded-cleanup-plan.md
source_digest: sha256:10ee1d8fa5a93fed03263bf563494a8c73c887f67b955b3dd6fc8f252e723d8f
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-04
created_provenance: git-commit
disposition_changed: 2026-09-04
disposition_changed_provenance: git-rename
run_id: ticket-autopilot-orphan-worktree-gc-wgc-v3-20260904
---

# Apply an exact guarded cleanup plan

Compiled from `docs/tickets/ticket-autopilot-orphan-worktree-garbage-collection/done/02-apply-exact-guarded-cleanup-plan.md`. Identity is `ticket:ticket-autopilot-orphan-worktree-garbage-collection/WGC-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-04** via `git-commit`
- Disposition changed: **2026-09-04** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-orphan-worktree-garbage-collection]]
- Blocked by: [[sources/ticket-ticket-autopilot-orphan-worktree-garbage-collection-wgc-01]] — `ticket:ticket-autopilot-orphan-worktree-garbage-collection/WGC-01`

## Run

Completed under autopilot run `ticket-autopilot-orphan-worktree-gc-wgc-v3-20260904`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-orphan-worktree-garbage-collection-wgc-02.md","payload_bytes":3818,"payload_sha256":"10ee1d8fa5a93fed03263bf563494a8c73c887f67b955b3dd6fc8f252e723d8f"}],"payload_bytes":3818,"payload_sha256":"10ee1d8fa5a93fed03263bf563494a8c73c887f67b955b3dd6fc8f252e723d8f","schema":1,"source_digest":"sha256:10ee1d8fa5a93fed03263bf563494a8c73c887f67b955b3dd6fc8f252e723d8f","source_identity":"ticket:ticket-autopilot-orphan-worktree-garbage-collection/WGC-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3818,"payload_sha256":"10ee1d8fa5a93fed03263bf563494a8c73c887f67b955b3dd6fc8f252e723d8f","schema":1,"source_digest":"sha256:10ee1d8fa5a93fed03263bf563494a8c73c887f67b955b3dd6fc8f252e723d8f","source_identity":"ticket:ticket-autopilot-orphan-worktree-garbage-collection/WGC-02"} -->
```markdown
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

```
