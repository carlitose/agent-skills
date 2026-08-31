# Ticket Autopilot Post-merge Integration-copy Reconciliation

## Artifact Graph

- Artifact ID: `spec:ticket-autopilot-post-merge-integration-copy-reconciliation`
- Role: `spec`
- Parent: [Post-merge equivalent-head reconciliation](ticket-autopilot-post-merge-equivalent-head-reconciliation.md)

## Type

Bug analysis and correction specification

## Status

Accepted follow-up to EHR-01

## Corrected Diagnosis

EHR-01 safely implemented the exact two-parent topology specified by its accepted contract and integrated through agent-skills PR #184. The first fresh consumer replay against Betsharemarket run `ec4e6242327c4025`, ticket `06`, failed closed before ledger mutation with:

`equivalent-head merge commit does not have the observed head as second parent`

Fresh local object readback and GitHub PR #248 observation establish a distinct topology:

- recorded base/head: `68494747513bde694e5abc0c8a10799c8d3ed93b` / `e8b9218de3395fb4addefadd148fc0727d3fdec9`;
- observed base/head: `aee709c33491f6478da85242c4710b5ebcd120a4` / `a109426f3e461c5c3bc1c656885efe808c5dcff7`;
- provider integration commit: `bcb9921614569549d2dd2d059bc6508b3383c48f`;
- the observed head has exactly one parent, the observed base;
- the provider integration commit also has exactly one parent, the same observed base;
- the observed head and provider integration commit are distinct sibling commits with the same tree `189eb4839395cfbd3f55f8af724748ae7419e530`;
- the recorded, observed, and integration-copy transitions are the same non-empty eight-entry full-index raw transition with SHA-256 `21cabad17ea1144602fc2b75700d24669a8c3839fe21ed06c37a9d2fdff8a070`;
- terminal `main` reaches the integration commit, not the provider-reported PR head.

The earlier specification incorrectly described this historical integration commit as a two-parent merge. EHR-01 remains correct for its declared shape; it does not cover this sibling integration-copy shape. The failed replay did not append a receipt, change ticket 06's head/lineage, resolve its provider gate, or mutate GitHub.

## Decision

Extend exact equivalent-head proof with one additional topology named `single-parent-integration-copy`. It is accepted only when every existing repository/provider/PR/branch, object, replacement-object, non-empty raw-transition, persistence, replay, and terminal-proof invariant holds and all of the following are exact:

1. The recorded head is one commit on the recorded base.
2. The observed provider head is a different one-commit delivery on an advanced observed base.
3. The provider integration commit differs from the observed head and has exactly the observed base as its only parent.
4. The observed head also has exactly that observed base as its only parent.
5. The observed head tree and integration commit tree are byte-identical tree objects.
6. The recorded-base-to-recorded-head, observed-base-to-observed-head, and observed-base-to-integration-commit raw streams from `git diff-tree -r --no-commit-id --raw --full-index --no-renames -z` are non-empty and byte-identical.
7. Every proof command disables Git replacement objects. Missing objects remain exact-SHA, no-tag, no-`FETCH_HEAD`, no-tracking-ref fetches with commit readback.
8. Fresh provider readback still reports the exact PR, branch, base branch, observed head, integration commit, and merged state before and after receipt persistence.
9. Ordinary terminal proof establishes that the exact integration commit is reachable from the fresh terminal branch. The sibling observed head need not itself be terminal-reachable.

The existing `two-parent-head-merge` topology remains unchanged. Any other shape fails closed: a changed base between observed head and integration commit, a multi-commit delivery, a two-parent merge with the wrong second parent, an octopus merge, an integration commit with multiple or no parents, tree drift, empty transition, raw-entry drift, or provider identity drift.

Provider merge-method labels, commit messages, patch IDs, textual similarity, path-only equality, and user assertion are not evidence. A general squash or multi-commit integration remains out of scope. This decision accepts only an exact one-commit sibling integration copy; if a provider labels an indistinguishable one-commit operation differently, the exact object and transition contract—not the label—controls.

## Receipt and Compatibility

Increment newly built equivalent-head receipts to schema 2 and add a required topology discriminator:

- `two-parent-head-merge`; or
- `single-parent-integration-copy`.

All existing identity, tree, raw digest/count, provider observation, actor, and evidence bindings remain. The integration commit SHA/tree already retained in the receipt bind the terminal object. Schema-2 proof computes all three raw streams before adoption.

Ledger loading and exact replay must continue to validate historical schema-1 `two-parent-head-merge` receipts without rewriting them. New proof never emits schema 1. A schema, field-set, topology, digest, head, base, or integration-commit mismatch is contradictory rather than migratable.

## Transaction and Authority Boundaries

The EHR-01 transaction ordering remains unchanged:

1. observe merged provider state;
2. read exact objects and prove one accepted topology;
3. append the receipt, update only current PR/delivery-lineage head, and clear stale merge authorization;
4. save and read back the protected ledger;
5. repeat exact provider readback;
6. resolve only matching provider-merge gates after terminal proof;
7. record ordinary external integration.

Proof remains read-only and grants no provider mutation, merge, reconciliation choice, completion projection, publication, issue, wiki, Pi, status-change, or human-start authority. A crash before receipt save leaves the ledger unchanged; a crash after save replays only the same schema/topology/receipt.

## Existing-run Recovery

After this follow-up integrates and the exact integrated runner head is synchronized locally, Betsharemarket ticket `06` may replay its ordinary `integrate` event. No caller supplies head, merge, receipt, topology, gate, or provider state. The runner owns fresh GitHub readback, proof, adoption, terminal reachability, provider-gate resolution, and integration.

Ticket `08` becomes dependency-ready only if ticket `06` reaches ordinary `integrated`. Human start gate `gate:08:start:4` remains open and cannot be satisfied by dependency recovery. The existing failed replay is retained as failure evidence; no Betsharemarket ledger or ticket source is manually edited.

## Acceptance Criteria

- The historical Betsharemarket object topology is reproduced in a disposable real Git repository, including distinct observed/integration sibling commits and terminal reachability of only the integration commit.
- Schema-2 proof accepts that shape only when all three raw transitions are non-empty and byte-identical.
- Existing two-parent proof remains accepted and emits schema 2 with `two-parent-head-merge`.
- Historical schema-1 two-parent receipts remain loadable and exactly replayable without rewriting.
- Wrong integration parent/base, equal observed/integration SHA, tree drift, raw drift, extra commit, replacement-ref spoofing, and provider-readback drift fail before adoption or integration as appropriate.
- Receipt persistence remains crash-safe and idempotent; forged schema/topology/history combinations fail ledger validation.
- Terminal proof records the reachable integration commit for the sibling topology and never treats provider `MERGED` or receipt adoption as integration.
- Existing exact-head integration creates no equivalent receipt, and EHR-01 two-parent behavior does not regress.
- Full Ticket Autopilot, verification-audit, llm-wiki, extension, forward, static, context-budget, and Artifact Graph delta checks pass.
- The consumer replay is performed only after integration and local sync; it leaves `gate:08:start:4` open.

## Out of Scope

- General squash, multi-commit rebase, queue rewrite, conflict-resolved integration, octopus merge, or arbitrary same-tree commits.
- Provider-method inference from messages, labels, UI text, or branch deletion.
- Patch-ID-only, final-tree-only, changed-path-only, or user-asserted equivalence.
- Manual Betsharemarket ledger, gate, source, branch, PR, or lineage mutation.
- Starting ticket 08, publishing runner-defect issues, resuming the status-change frontier before recovery, or reloading the active Pi session.
