# Ticket Autopilot Tracked Completion Reconciliation Candidate Binding

## Artifact Graph

- Artifact ID: `spec:ticket-autopilot-tracked-completion-reconciliation-candidate-binding`
- Role: `spec`
- Standalone: true

### Children

- [TCR-01 — Bind conflict proposals to the completion-projected delivery candidate](../tickets/ticket-autopilot-tracked-completion-reconciliation-candidate-binding/01-bind-conflict-proposals-to-the-delivery-candidate.md)

## Type

Bug analysis and correction specification

## Status

Ready for implementation

## Observed behavior

A tracked-source ticket can verify successfully, project its source ticket and completion
summary, commit and push, and open a PR. If `main` advances before merge and the delivery
commit conflicts, repository autonomous reconciliation should accept one exact proposal
bound to the branch tree. Instead, no proposal can pass validation.

The concrete RD-04 delivery demonstrated the mismatch:

- semantic CandidateRef tree: `68fb061e12c226b1ff387fbc2632d683f9322533`;
- completion-projected delivery tree: `42e8a00501d44f8d47941bd3505664feb72e6bcd`;
- conflict proposal `old_local_tree`: `42e8a00501d44f8d47941bd3505664feb72e6bcd`.

The resolver builds proposal context from `ticket["candidate_ref"]`, while proposal
validation also requires `candidate_ref.candidate_tree_oid == old_local_tree`. A proposal
using the semantic CandidateRef fails the tree equality. A proposal using the delivery
CandidateRef fails exact context equality.

## Expected behavior

Repository reconciliation proposals bind the exact branch state that is being rebased.
When a tracked completion projection has produced `delivery_candidate_ref`, the proposal
context and validator use that delivery CandidateRef. When no delivery candidate exists,
the existing semantic CandidateRef remains the fallback. Proposal application still
invalidates stale evidence and follows the normal revalidation, guarded publication, and
merge paths.

## Diagnosis Report - lens: single-pass

### Root cause

`autopilot.cli._reconciliation_conflict_resolver` supplies the pre-finalization semantic
CandidateRef as an exact proposal-context field, but
`autopilot.repository_reconciliation_authority.load_proposal` requires that same field's
candidate tree to equal the Git-observed old local tree. Tracked finalization changes the
branch tree by moving the ticket and adding its completion summary, so the two required
values differ and the proposal contract is unsatisfiable.

### Evidence

- The RD-04 branch head tree is `42e8a005…`, while its ledger retains semantic candidate
  tree `68fb061e…` and separately records delivery candidate tree `42e8a005…`.
- A schema-valid proposal using the semantic candidate reaches
  `reconciliation proposal CandidateRef is invalid`.
- Changing only the proposal CandidateRef to the delivery candidate reaches
  `reconciliation proposal candidate_ref drifted` because the resolver context still
  carries the semantic candidate.
- The repository reconciliation grant is active, exact, and unrevoked; target and remote
  heads match the persisted reconciliation intent. Missing authority and head drift are
  therefore not the cause.

### Feedback loop built

A provider-free direct `load_proposal` fixture binds the exact RD-04 grant and reconciliation
context. It proves both sides of the contradiction: semantic candidate is tree-invalid;
delivery candidate is context-invalid. The production integration test must additionally
create a tracked completion projection, force a real bounded rebase conflict, submit the
exact delivery-bound proposal, and observe adoption/application before fresh revalidation.

### Fix location and approach

Change the conflict-resolver proposal context to select the exact
`delivery_candidate_ref` when present, falling back to `candidate_ref` for runs without a
separate delivery candidate. Keep every existing proposal field, grant check, conflict
allowlist, patch digest, result-tree check, gate consumption, and post-application
revalidation invariant unchanged.

### Alternatives ruled out

- Provider mergeability is not the root cause: the failure occurs while deriving the local
  reconciliation candidate before any replacement-head provider mutation.
- The proposal is not merely absent: each of the only two possible CandidateRef choices is
  rejected by a different mandatory equality.
- Reusing the semantic tree as `old_local_tree` is unsafe because it would not bind the
  committed and pushed branch state that Git is actually rebasing.
- Removing CandidateRef validation would weaken authority and tree identity unnecessarily;
  the already recorded delivery CandidateRef is the exact missing identity.

### Confidence: high

The contradiction is reproduced directly against the validator with exact real run values,
and the two incompatible predicates are explicit in the current production call path.

## Goals

- Make tracked completion-projected delivery conflicts eligible for the existing exact
  repository reconciliation proposal flow.
- Bind authority to the actual old branch tree without weakening semantic CandidateRef or
  delivery-lineage checks.
- Preserve provider, merge, gate, source, completion, wiki, Pi, and cleanup authorities as
  separate capabilities.
- Revalidate any reconciled result through the existing candidate quality pipeline.

## Non-goals

- Automatic semantic conflict choices without an exact proposal.
- Changing completion projection content or authority.
- Approving a reconciliation gate without the active repository grant and exact proposal.
- Reusing old review, QA, verification, PR-body, or merge evidence after semantic drift.
- Changing provider merge eligibility, issue publication, or RD-05 authority.

## Semantic invariants

1. A proposal CandidateRef identifies the exact old local tree being rebased.
2. A tracked completion projection uses `delivery_candidate_ref`; an absent delivery
   projection uses the existing semantic `candidate_ref`.
3. Proposal grant, repository, remote, ticket digest, branch, old/new head and tree,
   conflict path, resolution blob, patch digest, and result tree checks remain exact.
4. Proposal application consumes only covered reconciliation gates and records adoption and
   application receipts; it does not manufacture human approval.
5. The result receives a fresh CandidateRef and complete required revalidation before push,
   PR update, or merge.
6. No issue-publication, merge, completion-projection, wiki, Pi, source, cleanup, or other
   authority transfers through this fix.

## Failure modes

| Failure | Required result |
|---|---|
| Delivery candidate missing | Use the semantic candidate fallback and preserve existing behavior. |
| Delivery candidate malformed or stale | Fail existing ledger/proposal validation before application. |
| Delivery candidate tree differs from old local tree | Reject the proposal. |
| Target, remote head, branch, ticket digest, or grant drifts | Reject before worktree mutation. |
| Proposal resolves extra paths or leaves markers/unmerged entries | Reject and recover to the guarded old head. |
| Revalidation fails after application | Keep the ticket gated; do not publish or merge. |
| Reconciliation grant is revoked | Block application and every dependent provider mutation. |

## Compatibility

This is an internal schema-4 correction. Proposal schema, authority files, existing receipts,
semantic CandidateRef v2, and runs without `delivery_candidate_ref` remain compatible. No
migration or legacy alias is introduced.

## Implementation slice

One ticket owns:

- selecting the delivery CandidateRef at proposal-context construction;
- unit coverage for selection and fail-closed mismatch;
- a disposable tracked-source conflict scenario covering completion projection through
  proposal application and fresh revalidation;
- regression, forward, context, and Artifact Graph checks; and
- concise operator/contract wording only if the behavior is not already clear.

## Acceptance outcomes

1. The exact two-sided contradiction fixture fails before the change and passes with the
   delivery CandidateRef selected.
2. A tracked completion-projected branch with a real bounded conflict accepts an exact
   authorized proposal whose old local tree equals `delivery_candidate_ref`.
3. The same proposal with the semantic CandidateRef, wrong tree, wrong grant, target drift,
   remote drift, extra path, or changed blob fails before application.
4. Runs without a delivery candidate preserve existing proposal behavior.
5. After application, old quality and merge evidence are not reused; fresh revalidation is
   required before provider mutation.
6. The previously blocked RD-04 proposal can be represented canonically after the fix
   integrates; no manual conflict or gate bypass is needed.

## Verification strategy

### Unit

- Candidate selection with delivery present and absent.
- Semantic/delivery tree mismatch and malformed/stale delivery candidate rejection.
- Exact proposal context, grant, path, digest, and result-tree validation.

### Integration

- Disposable tracked ticket finalization that moves the ticket and adds a completion
  summary, followed by target advancement, bounded conflict, exact proposal adoption,
  application, and fresh CandidateRef invalidation.
- Replay, revocation, remote/target drift, and interrupted-rebase recovery.

### Regression

- Full Ticket Autopilot tests, extension tests, forward scenarios, Python/static checks,
  controlled context measurement, and Artifact Graph baseline/candidate comparison.

### Live boundary

No live provider mutation is required to prove this correction. RD-04 merge remains a
separate exact-head provider action after the fix integrates and its proposal is applied.
