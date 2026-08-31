# Ticket Autopilot Post-merge Equivalent-head Reconciliation

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-post-merge-equivalent-head-reconciliation`
- Role: `specification`
- Status: Accepted
- Source diagnosis: Betsharemarket run `ec4e6242327c4025`, ticket `06`, GitHub PR `carlitose/betsharemarket#248`

## Problem

Ticket Autopilot binds delivery, authorization, provider readback, and terminal integration to an exact commit SHA. That fail-closed rule prevents unreviewed code from being accepted. It also leaves one safe external-merge case without a transition: the provider may merge a rebased single-commit head whose exact tree-entry delta is identical to the recorded delivery head, while the ledger still names the pre-rebase SHA.

The reproduced Betsharemarket sequence is:

- recorded delivery base/head: `68494747513bde694e5abc0c8a10799c8d3ed93b` / `e8b9218de3395fb4addefadd148fc0727d3fdec9`;
- provider merge base/head: `aee709c33491f6478da85242c4710b5ebcd120a4` / `a109426f3e461c5c3bc1c656885efe808c5dcff7`;
- provider merge commit: `bcb9921614569549d2dd2d059bc6508b3383c48f`;
- both heads are single commits with their respective base as the only parent;
- the full `git diff-tree -r --no-commit-id --raw --full-index --no-renames -z <base> <head>` byte stream has SHA-256 `21cabad17ea1144602fc2b75700d24669a8c3839fe21ed06c37a9d2fdff8a070` for both pairs;
- the stream covers identical paths, before/after modes, before/after blob OIDs, additions, deletion, and the ticket completion projection;
- GitHub reports PR #248 merged at the provider head, while the ledger retains the recorded head and therefore opens a provider-merge gate.

This is not ledger corruption and is not missing merge authorization. The ledger preserves the historical fact it knew. The missing capability is a bounded post-merge adoption transaction that proves equivalence before replacing the current delivery lineage.

## Decision

Add a post-merge **exact tree-transition equivalence** transaction. It may adopt a provider-observed head only when all of the following are proven from fresh provider and Git readback:

1. The run has a recorded PR and versioned delivery lineage for the same provider, PR ID, branch, and base branch.
2. The provider reports that exact PR as merged, with a non-empty different head and merge commit.
3. The recorded head and observed head are each single commits.
4. The recorded head's only parent is the recorded delivery base.
5. The merge commit has exactly two parents: the observed base first and the observed head second.
6. The observed head's only parent is that same observed base.
7. Both base/head pairs and the merge commit exist as commits in the repository object database. Missing objects may be fetched by exact SHA without moving a remote-tracking ref or writing `FETCH_HEAD`.
8. The canonical full-index, no-rename, NUL-delimited raw tree-transition byte streams are non-empty and byte-identical.
9. The raw transition therefore binds the same path set, status, file types, modes, old blob OIDs, and new blob OIDs. Patch ID alone is never sufficient.
10. The provider branch/base and the observed commit topology match the recorded PR identity. A squash, rebase-and-merge without the observed head, octopus merge, merge queue rewrite, multi-commit delivery, ambiguous parent, touched-path baseline change, mode change, extra path, or any missing readback fails closed.

The transaction does not rewrite historical delivery steps. It appends one integrity-checked equivalence receipt, updates only the current PR head and delivery-lineage head, clears any stale merge authorization, and emits a dedicated ledger event. The receipt retains both base/head pairs, their trees, merge commit and tree, raw-delta digest and entry count, provider observation digest, repository identity, actor, evidence, and contract version.

After the equivalence receipt is durably saved and read back, the existing external integration path runs unchanged against the adopted provider head. It must still prove fresh terminal-branch reachability. Provider `MERGED`, raw-delta equivalence, or patch equivalence alone never marks a ticket integrated.

## Transaction Ordering and Replay

1. Hold the canonical run lock.
2. Read the integrity-wrapped ledger and exact recorded PR/delivery lineage.
3. Fetch one fresh provider PR observation; require merged state and different head.
4. Observe/fetch exact Git objects without moving delivery or remote-tracking refs.
5. Build and validate the equivalence receipt from the two parent/head pairs and merge topology.
6. Append the receipt, update only current PR/delivery-lineage head, clear stale merge authorization, emit the dedicated event, save the ledger, and read it back.
7. Re-fetch or revalidate provider state under the same run transaction.
8. Build the ordinary external terminal-integration proof for the adopted head.
9. Consume only matching provider-merge gates and record ordinary external integration.

A crash before step 6 leaves the ledger unchanged. A crash after step 6 replays the exact receipt and continues ordinary external integration. Any later provider/head/topology/delta contradiction stops without a second adoption. The original recorded head remains recoverable from the immutable receipt and earlier history.

## Interface

The existing `resume` integration operation is the production seam. When a merged provider observation differs from the recorded head, it attempts exact equivalent-head proof instead of immediately returning `external merge reconciliation head SHA is stale`. No new merge, reconciliation, publication, issue, wiki, Pi-sync, or status-change authority is inferred.

Successful output identifies:

- recorded and adopted heads;
- equivalence receipt digest;
- terminal proof digest;
- whether equivalence adoption and integration were replayed;
- final ticket state.

Failure reports the first exact failed invariant. It must never downgrade to patch ID, textual similarity, tree-only equality, or user assertion.

## Existing-run Recovery

Compatibility is explicitly limited to existing schema-4 runs whose ledger validates under its original exact-head contract and whose provider/Git evidence satisfies every invariant above. No migration or ledger rewrite is permitted. Betsharemarket ticket 06 is the causal recovery fixture; after the updated runner is integrated and locally synchronized, its run may replay the normal `integrate` event. Ticket 08 may become dependency-ready only after ticket 06 receives ordinary external terminal integration. Its separate `gate:08:start:4` human start authority remains open and is not satisfied by this recovery.

## Acceptance Criteria

- A rebased single-commit provider head with an exactly identical raw tree transition is adopted and then integrated only after fresh terminal reachability.
- Any changed path, status, file mode/type, old blob, new blob, parent, branch, base branch, PR ID, provider, merge topology, or provider observation fails closed.
- Patch-ID-only equality, same final candidate subtree, or same commit message cannot authorize adoption.
- The equivalence receipt is strict, deterministic, integrity-validated on ledger load, append-only, and idempotent across crashes before/after its save.
- Historical delivery metadata is not rewritten; only current PR/delivery-lineage head and stale merge authorization may change in the adoption event.
- Existing exact-head integration remains unchanged and does not create an equivalence receipt.
- Provider mutation is impossible in the equivalence path; only read-only provider/Git observations occur before ordinary external integration readback.
- Tests include real disposable Git repositories for the Betsharemarket topology, malicious near-misses, missing objects, crash replay, forged ledger history, and terminal-proof failure.
- Full Ticket Autopilot, extension, forward, static, context-budget, and Artifact Graph checks pass without representing historical Betsharemarket evidence as fresh execution.
- No live GitHub issue operation occurs.

## Out of Scope

- Multi-commit, squash, queue-rewritten, octopus, or conflict-resolved rebases.
- Equivalence based only on patch ID, textual diff, commit message, final tree, or changed path names.
- Automatic repair of arbitrary stale PR heads before merge.
- Manual ledger edits, gate waivers, fabricated merge authority, or default-branch mutation.
- Starting Betsharemarket ticket 08 without its exact human gate.
- Runner-defect issue publication, status-change delivery, wiki synchronization, or Pi reload.
