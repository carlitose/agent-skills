---
type: source
title: "Register ownership and plan orphan cleanup"
identity_key: ticket:ticket-autopilot-orphan-worktree-garbage-collection/WGC-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-orphan-worktree-garbage-collection/done/01-register-and-plan-orphan-cleanup.md
source_digest: sha256:66b302ec242837b226da5e8299e49eecfeeb0d10b0a827f033e306a23cf4871b
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-04
created_provenance: git-commit
disposition_changed: 2026-09-04
disposition_changed_provenance: git-rename
run_id: ticket-autopilot-orphan-worktree-gc-wgc-v3-20260904
---

# Register ownership and plan orphan cleanup

Compiled from `docs/tickets/ticket-autopilot-orphan-worktree-garbage-collection/done/01-register-and-plan-orphan-cleanup.md`. Identity is `ticket:ticket-autopilot-orphan-worktree-garbage-collection/WGC-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-04** via `git-commit`
- Disposition changed: **2026-09-04** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-orphan-worktree-garbage-collection]]

## Run

Completed under autopilot run `ticket-autopilot-orphan-worktree-gc-wgc-v3-20260904`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-orphan-worktree-garbage-collection-wgc-01.md","payload_bytes":3993,"payload_sha256":"66b302ec242837b226da5e8299e49eecfeeb0d10b0a827f033e306a23cf4871b"}],"payload_bytes":3993,"payload_sha256":"66b302ec242837b226da5e8299e49eecfeeb0d10b0a827f033e306a23cf4871b","schema":1,"source_digest":"sha256:66b302ec242837b226da5e8299e49eecfeeb0d10b0a827f033e306a23cf4871b","source_identity":"ticket:ticket-autopilot-orphan-worktree-garbage-collection/WGC-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3993,"payload_sha256":"66b302ec242837b226da5e8299e49eecfeeb0d10b0a827f033e306a23cf4871b","schema":1,"source_digest":"sha256:66b302ec242837b226da5e8299e49eecfeeb0d10b0a827f033e306a23cf4871b","source_identity":"ticket:ticket-autopilot-orphan-worktree-garbage-collection/WGC-01"} -->
```markdown
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

```
