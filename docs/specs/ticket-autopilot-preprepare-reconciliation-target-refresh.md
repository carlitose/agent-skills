# Ticket Autopilot Pre-prepare Reconciliation Target Refresh

## Artifact Graph

- Artifact ID: `spec:ticket-autopilot-preprepare-reconciliation-target-refresh`
- Role: `spec`
- Standalone: true

### Children

- [PRT-01 — Refresh a conflict-blocked reconciliation intent before prepare](../tickets/ticket-autopilot-preprepare-reconciliation-target-refresh/done/01-refresh-conflict-blocked-intent-before-prepare.md)

## Type

Bug analysis and correction specification

## Status

Ready for implementation

## Observed behavior

The runner persists `delivery.reconcile-intent` before attempting a rebase. If that rebase
conflicts, no `reconcile-prepare` exists yet. While the exact conflict proposal is being
prepared, another integrated PR can advance the target branch. The next reconciliation
fetches the new target, compares it to the old immutable intent, and stops with:

`reconciliation target changed after durable intent`

The existing target-refresh path runs only after `reconcile-prepare` exists. Therefore a
conflict-blocked initial intent cannot reach either the exact proposal resolver or the
existing prepared-candidate refresh path.

RD-04 demonstrated the production state:

- persisted target: `53293699e3218e6cdb045e640d43ae79e7a26922`;
- current target after TCR-01 integration: `15ee33d31e0ecd18209938a44c7ae67745d2a963`;
- old local/remote head remains exact: `a3d4226a4f0f4ed5b71e4b1f4d925a93a6c70672`;
- no reconciliation push, retarget, or provider mutation occurred;
- the active exact repository reconciliation grant remains unrevoked.

## Expected behavior

Before provider mutation and before a prepared reconciliation candidate exists, the runner
may refresh only the fetched target portion of an otherwise identical reconciliation
intent. It persists the old and replacement intents before retrying Git, supports repeated
target advances without erasing history, and consumes the pending refresh only after the
exact rebase/proposal result is read back into `reconcile-prepare`.

Any drift in branch, old head, parent, expected remote head, target branch/ref identity, run,
ticket, grant, or source mode remains fail-closed. Prepared or provider-mutated attempts
continue through the existing later refresh path and are not widened.

## Diagnosis Report - lens: data-flow

### Root cause

The `reconcile` event's initial branch compares the newly fetched intent with
`delivery.reconcile-intent` and raises before `_derive_reconciliation_candidate`. The only
replacement-intent transaction is in the later publication branch and requires both
`reconcile-prepare` and `reconcile-refresh-intent`. A conflict occurs after intent
persistence but before prepare, leaving no legal state transition that can update the exact
target or invoke the proposal resolver.

### Evidence

- RD-04 now opens `stack-reconciliation` gate `gate:RD-04:dynamic:6` with the exact target
  change message before entering the fixed proposal CandidateRef selector.
- Its old local and remote heads remain equal, its worktree is clean, and the provider PR
  head is unchanged, ruling out branch divergence.
- Current code raises on `existing_intent != intent` in the `prepared is None` branch.
- Current target-refresh construction and replacement occur only in the `prepared is not
  None` branch and `Kernel.prepare_reconciliation` requires a prior prepare for refresh.

### Feedback loop built

The production RD-04 ledger plus a provider-free reconciliation replay deterministically
reaches the target-change gate. The implementation test must use a disposable remote: persist
an intent, force a conflict before prepare, advance target one or more times, persist exact
refresh lineage, apply an authorized proposal, and prove prepare consumes the newest target
without provider mutation or lost history.

### Fix location and approach

Add a pre-prepare target-refresh transaction across the CLI orchestration and kernel. It
validates that only target SHA/tree advanced, records old/replacement intent (and any
superseded pending refresh) before Git mutation, drives the normal exact proposal resolver
against the newest target, and atomically archives/installs the replacement intent when
`reconcile-prepare` is created.

### Alternatives ruled out

- Manual deletion or replacement of `reconcile-intent` would erase crash history and bypass
  runner authority.
- Applying a proposal to the stale target outside the runner would omit adoption/application
  receipts and still require another refresh.
- Existing prepared-candidate refresh cannot run because conflict prevented
  `reconcile-prepare` from being created.
- Provider merge, merge authority, or repository reconciliation authority alone cannot
  rewrite persisted scheduler intent.

### Confidence: high

The exact production gate and mutually exclusive branches are observed; no competing head,
source, provider, or authority drift is present.

## Goals

- Let an exact initial reconciliation intent follow target advancement while conflict-gated.
- Preserve immutable old intent, every pending replacement, and exact Git/proposal readback.
- Support repeated target advances before proposal application.
- Keep prepared-candidate refresh and every provider/merge/authority boundary unchanged.
- Unblock canonical RD-04 reconciliation without manual ledger or branch mutation.

## Non-goals

- Changing conflict content without an exact authorized proposal.
- Refresh after reconciliation push, retarget, queue, merge, or other provider mutation.
- Replacing any non-target intent field.
- Weakening ticket source, CandidateRef, proposal, grant, remote-head, or result-tree checks.
- Granting merge, issue publication, completion projection, wiki, Pi, cleanup, or source
  authority.

## Semantic invariants

1. The old persisted intent is never overwritten without append-only refresh lineage.
2. Only `target_base.sha` and `target_base.tree_oid` may change; target branch/ref and all
   non-target fields remain exact.
3. A pending pre-prepare refresh is persisted before rebase or proposal application.
4. Repeated advances archive the superseded pending replacement before installing the next.
5. The pending replacement becomes canonical only when exact Git result readback creates
   `reconcile-prepare`.
6. Existing conflict proposal adoption/application and gate-consumption rules remain exact.
7. No provider mutation can occur before fresh review, QA, verification, finalization,
   PR-body validation, checks, approvals, and mergeability.
8. Prepared-candidate target refresh retains its existing schema and behavior.

## Failure modes

| Failure | Required result |
|---|---|
| Non-target intent field changes | Reject before worktree mutation. |
| Target branch or ref identity changes | Reject before worktree mutation. |
| Remote/local PR head drifts | Reject through existing exact-head guards. |
| Provider mutation already exists | Reject pre-prepare refresh. |
| Pending refresh is malformed or contradictory | Gate without replacing it. |
| Target advances repeatedly | Append prior pending refresh to history and bind the newest exact target. |
| Rebase/proposal remains conflicted | Keep pending refresh and visible gate for exact replay. |
| Proposal or result tree drifts | Recover/abort through existing authority flow; do not install replacement intent. |
| Crash after prepare transaction | Replay observes canonical replacement intent and exact prepare once. |

## Compatibility

No ticket, CandidateRef, repository-grant, or proposal schema changes. One new internal
pre-prepare refresh record/history is additive. Existing runs without target drift and the
later `reconcile-refresh-intent` path remain behaviorally identical.

## Acceptance outcomes

1. The production-shaped no-prepare target-change reproduction fails before the change and
   proceeds to the conflict/proposal boundary after it.
2. Only target SHA/tree drift is accepted; every other intent difference fails before Git.
3. Old intent and repeated pending replacements remain append-only and exact.
4. An exact authorized proposal against the newest target applies, records receipts, creates
   prepare, installs the replacement intent, and requires normal semantic revalidation.
5. Crash/replay at refresh persistence, proposal application, and prepare installation is
   idempotent.
6. Provider mutation before fresh quality remains impossible.
7. RD-04 can represent the latest target canonically after this fix integrates.

## Verification strategy

### Unit

- Exact target-only delta validation and non-target/branch/ref rejection.
- Pending refresh creation, repeated replacement history, malformed state, and idempotent
  replay.
- Kernel consumption installs replacement intent and appends immutable history once.

### Integration

- Disposable remote, persisted initial intent, real conflict, multiple target advances,
  active repository reconciliation grant, exact proposal, prepare readback, and fresh quality
  invalidation.
- Crash points before Git, after proposal application, and during prepare persistence.

### Regression

- Full Ticket Autopilot suite, extensions, forward scenarios, changed Python compilation,
  diff/tree checks, controlled context, and Artifact Graph baseline/candidate delta.

### Live boundary

No live provider mutation is required for verification. RD-04 provider publication and merge
remain separate after the fix integrates and its exact proposal applies.
