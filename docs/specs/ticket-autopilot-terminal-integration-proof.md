# Ticket Autopilot terminal integration proof

## Artifact Graph

- Artifact ID: `spec:ticket-autopilot-terminal-integration-proof`
- Role: `spec`
- Standalone: true

### Children

- [TIP-01 — Prove terminal reachability before integration](../tickets/ticket-autopilot-terminal-integration-proof/01-prove-terminal-reachability-before-integration.md)

## Type

Bug analysis and focused feature specification.

## Problem

Ticket Autopilot currently treats a provider `MERGED` observation for the recorded PR head as sufficient integration evidence. In a stacked run, a child PR can be merged into an obsolete parent branch that is no longer destined for the terminal branch. The provider reports the child PR as merged, and both the live orchestration path and replay can mark the child `integrated`, even though neither the child head nor its provider merge commit is reachable from terminal `main`.

The same model leaves an externally merged root parent ledger-gated when no replay-safe autonomous merge attempt preceded the provider merge. That blocks a child from entering the existing stack reconciliation path even when fresh provider and Git evidence prove the parent is already on the terminal branch.

Observed anchors are the integration transition and replay paths in `ticket-autopilot/scripts/autopilot/cli.py` and `kernel.py`, including the existing provider-state readback, stack retarget, and `record_integration` seams. The reproduced failure merged a child into obsolete `stack/07` and still reached `integrated`.

## Current behavior

- Provider state `merged` plus an exact recorded PR head can produce `integrated`.
- Integration does not persist the terminal branch tip/tree used for the decision.
- Integration does not prove the recorded head or provider merge commit is an ancestor of the freshly fetched terminal branch.
- `merge-all` gates an already-provider-merged ticket if no replay-safe autonomous attempt exists, even when read-only provider/Git proof could reconcile terminal truth.
- A child remains blocked from reconciliation while such a parent is ledger-gated and can retain an obsolete stack base.
- Replay duplicates enough transition logic to accept impossible or stale terminal states.

## Target behavior

### Terminal delivery target

Every deliverable ticket has one derived terminal target branch. For a root ticket this is its recorded delivery base. For a stack child it is the recursively inherited root delivery base, not merely its immediate parent branch. The terminal branch name and fresh remote SHA/tree are part of the integration proof.

### Integration proof

Before any live, autonomous, manual, external-readback, or replay path records `integrated`, the runner must:

1. read the recorded PR from the provider and match provider, repository, PR id, and exact recorded head;
2. derive the expected terminal target from persisted delivery lineage;
3. fetch that exact remote terminal branch without accepting a stale local ref;
4. prove that either the exact PR head or the provider-reported merge commit is an ancestor of the fetched terminal tip;
5. persist a canonical proof receipt containing the expected terminal branch, observed terminal SHA/tree, PR base, exact head, merge commit when available, which object proved reachability, provider observation identity, and proof version;
6. re-read and validate that receipt during replay before accepting `integrated`.

Provider `MERGED` without this terminal proof remains non-integrated. A missing merge commit is acceptable only when the exact PR head itself is reachable. Unsupported provider data, missing objects, remote drift during proof, or failed ancestry checks fail closed as `reconciliation-required` or an explicit gate without fabricating approval.

### External parent reconciliation

A provider-merged root or parent that lacks a replay-safe autonomous attempt may be reconciled read-only when the same exact terminal proof succeeds. This records historical integration truth, not autonomous merge authorization and not evidence that the runner performed the merge. It must retain provenance distinguishing `external-readback` from runner-initiated merge.

Once every blocker has a valid terminal proof, a stacked child must use the existing reconciliation/retarget path to move away from an obsolete stack base before any subsequent merge attempt. A child already merged into an obsolete branch remains non-integrated until its head or provider merge commit becomes reachable from the terminal target.

## Semantic invariants

- Provider `MERGED` is necessary but never sufficient for terminal integration.
- Exact terminal reachability is required for every integration entry point and replay.
- Terminal proof is repository-, provider-, PR-, head-, lineage-, branch-, tip-, and tree-bound.
- Fresh fetch and ancestry are Git object/index truth; conversation state is not evidence.
- Read-only external reconciliation grants no provider mutation or merge authority.
- Repository merge authority still requires fresh checks, approvals, mergeability, queue/direct-mode checks, exact-head mutation, and provider readback.
- Repository reconciliation authority remains proposal-bound conflict authority and is not broadened by this work.
- Existing run-local grants are not overwritten.
- A stack child is never `integrated` solely because it was merged into an immediate or obsolete parent branch.
- Replay and kernel use one shared validator for the terminal proof rather than independently approximating the invariant.
- The separate precompleted-parent-without-lineage ledger defect is not repaired here unless the minimum shared validator extraction is required; its broader lifecycle redesign remains a separate ticket.

## Failure modes

- Terminal branch cannot be derived: fail closed with explicit lineage/reconciliation state.
- Provider receipt omits both a reachable head and usable merge commit: remain non-integrated.
- Terminal remote changes between fetch and persistence: retry from a new observation or gate; never reuse the stale proof.
- Provider PR base is an obsolete stack branch and neither head nor merge commit reaches terminal: classify reconciliation-required.
- A later parent merge makes the child reachable: a fresh proof may reconcile it idempotently.
- Receipt replay differs in any bound field or ancestry no longer reproduces: reject ledger replay as impossible state.
- Squash/rebase provider strategies: accept only a provider merge object proven reachable; never guess patch equivalence.

## Security and authority boundaries

This capability performs provider reads and bounded Git fetch/ancestry checks. It does not grant conflict selection, merge, push, retarget, source publication, bootstrap, wiki, Pi, cleanup, visibility, secret classification, or provider-policy authority. Provider mutation remains under existing exact-head guards. Receipts must not embed credentials or unsanitized provider output.

## Implementation slices

1. Add a canonical terminal-target derivation and terminal-integration-proof value/validator shared by live orchestration, kernel transition, and ledger replay.
2. Extend provider normalized PR readback with the merge commit identity needed for reachability without weakening existing receipt checks.
3. Require fresh remote fetch, exact ancestry proof, and persisted proof before `record_integration`, autonomous merge completion, external merged-state reconciliation, or replay acceptance.
4. Let `merge-all` reconcile an already-merged parent only through read-only terminal proof, preserving external provenance and leaving failed proof visible.
5. Route newly unblocked children through existing stack reconciliation/retarget and revalidation before merge.
6. Add real-Git stacked regressions for obsolete-base false integration, parent-later-reachable success, direct root merge, merge-commit reachability, exact-head reachability, remote drift, unsupported receipts, and replay corruption.
7. Update operator docs, forward scenarios, artifact audit expectations, and the controlled context budget.

## Verification strategy

- Unit tests for terminal-target derivation, proof schema, exact binding, idempotent replay, corruption, and provenance.
- Disposable real-Git integration tests that reproduce a child merged into an obsolete branch and prove it remains non-integrated.
- Positive real-Git cases for direct root merge and transitive reachability after the parent reaches `main`.
- Fake-provider orchestration tests for live/manual/autonomous/external-readback paths, fresh fetch drift, absent merge commit, and exact-head mismatch.
- Regression tests that distinct merge and reconciliation grants remain unchanged and non-merge gates are not consumed.
- Full Ticket Autopilot tests, forward scenarios, static checks, exact CandidateRef checks, artifact-audit delta, and controlled context measurement.
- Live GitHub behavior is limited to the existing provider readback during delivery; candidate QA must not overclaim production or independent evidence.

## Acceptance outcomes

- A child PR merged only into obsolete `stack/07` cannot become `integrated`.
- A provider-merged root parent whose exact head or merge commit is on `main` can be reconciled with explicit `external-readback` provenance and no merge mutation.
- An unblocked child is retargeted/rebased through the existing quality pipeline before a merge attempt.
- Every terminal integration state has a replay-valid canonical proof bound to a fresh terminal tip/tree.
- All integration entry points and replay reject provider-only merged evidence.
- Existing exact-head merge and proposal-bound conflict authority remain intact.

## Non-goals

- Redesigning all ledger lifecycle invariants or repairing the independent precompleted-parent lineage defect.
- Choosing conflict content or broadening repository reconciliation authority.
- Supporting patch-equivalence inference when neither provider head nor merge object is reachable.
- Changing merge strategy, branch protection, queue policy, or provider settings.
- Integrating the wiki or synchronizing Pi inside this implementation candidate.
