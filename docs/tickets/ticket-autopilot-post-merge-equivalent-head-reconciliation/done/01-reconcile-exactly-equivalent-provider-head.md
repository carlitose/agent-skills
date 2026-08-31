---
ticket_schema: 1
ticket_id: "EHR-01"
execution_mode: AFK
blocked_by: []
---

# Reconcile an exactly equivalent provider head after merge

## Artifact Graph

- Artifact ID: `artifact:ehr-01-post-merge-equivalent-head-reconciliation`
- Role: `ticket`
- Parent: [Ticket Autopilot Post-merge Equivalent-head Reconciliation](../../specs/ticket-autopilot-post-merge-equivalent-head-reconciliation.md)

## Parent Spec

[Ticket Autopilot Post-merge Equivalent-head Reconciliation](../../specs/ticket-autopilot-post-merge-equivalent-head-reconciliation.md)

## What to Build

Implement the bounded post-merge equivalent-head transaction from the parent spec. Prove an exact, non-empty, full-index raw tree transition across recorded and provider base/head pairs; persist an immutable equivalence receipt before changing current PR/delivery lineage; then reuse ordinary external terminal integration against the adopted head. Recover the reproduced Betsharemarket PR #248 shape without weakening exact-head integration or performing provider mutation.

## Acceptance Criteria

- [ ] A strict module observes/fetches exact commit objects without moving remote-tracking refs and validates single-commit/two-parent merge topology.
- [ ] Canonical NUL-delimited `diff-tree --raw --full-index --no-renames` streams must be non-empty and byte-identical, binding paths, status, modes, old blobs, and new blobs.
- [ ] Patch ID, commit message, final-tree similarity, path-only equality, and user assertion are never accepted as equivalence proof.
- [ ] The receipt binds repository, provider, PR, branch/base branch, recorded/observed bases and heads and trees, merge commit/tree, raw-delta digest/count, provider observation digest, actor, evidence, and contract version.
- [ ] One dedicated kernel/ledger event updates only current PR head, delivery-lineage head, stale merge authorization, and append-only equivalence metadata; historical delivery steps remain exact.
- [ ] Receipt persistence/readback precedes terminal proof and integration; crash before/after persistence replays without lost history or provider mutation.
- [ ] Exact-head external integration remains unchanged; adopted-head integration still requires fresh terminal-branch reachability.
- [ ] Negative tests cover every path/blob/mode/parent/branch/base/provider/PR/topology mismatch, multi-commit/squash/queue shapes, missing objects, forged receipt/history, and terminal-proof failure.
- [ ] A disposable real-Git fixture reproduces Betsharemarket's recorded/provider topology and exact raw-delta digest `21cabad17ea1144602fc2b75700d24669a8c3839fe21ed06c37a9d2fdff8a070` without claiming fresh execution against that repository.
- [ ] Full regressions, extension/forward scenarios, static/context checks, and Artifact Graph delta pass with no live provider mutation or GitHub issue operation.

## Frontier

Ready. This is a technical reconciliation correction, not merge authorization. Downstream Betsharemarket recovery occurs only after this runner ticket is integrated and locally synchronized.

## Step-by-Step Implementation Plan

1. Add strict equivalent-head proof generation/validation and object-only Git observation.
2. Add kernel receipt adoption plus exact ledger event/static/history validation.
3. Extend merged external integration to persist/read back adoption before terminal proof.
4. Add causal real-Git, provider, crash, forgery, and compatibility tests.
5. Run full quality gates and deliver the runner change through normal PR/terminal proof.

## Testing Plan

Use temporary repositories and simulated provider observations for all implementation tests. Reproduce the exact single-commit/two-parent topology, mutate one invariant at a time, and prove no provider mutation command is available in the equivalence stage. After runner integration, separately replay Betsharemarket ticket 06 with live read-only PR state and terminal Git proof.

## Out of Scope

- Multi-commit, squash, queue-rewritten, octopus, or conflict-resolved equivalence.
- Manual Betsharemarket ledger/gate/branch mutation.
- Starting ticket 08 or satisfying `gate:08:start:4`.
- Live issue publication, wiki synchronization, status changes, or Pi/session reload.
