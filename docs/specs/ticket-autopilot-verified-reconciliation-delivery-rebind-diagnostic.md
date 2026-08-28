# Ticket Autopilot Verified Reconciliation Delivery-Rebind Bug

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-verified-reconciliation-delivery-rebind-diagnostic`
- Role: `spec`
- Standalone: true

### Children

- [VR-01 rebind a verified reconciliation candidate](../tickets/ticket-autopilot-verified-reconciliation-delivery-rebind/done/01-rebind-verified-reconciliation-candidate.md)

## Type

Diagnostic spec

## Status

Fixed and covered by VR-01 regression tests.

## Diagnosis Report - lens: single-pass

### Root cause

After semantic reconciliation invalidated an old candidate, a later implementation correction
could be adopted and fully verified before publication. `candidate_ref` then named the corrected
tree, while `delivery_candidate_ref`, `reconcile-prepare.candidate_ref`, and the prepared
`new_head` still named the earlier tree. The `reconcile` resume path compared Git only with the
delivery candidate and called the generic revalidation transition. That transition attempted to
destroy already valid evidence without changing `candidate_ref`, so the ledger correctly rejected
it. Updating only the delivery binding would also have been unsafe because the prepared commit
still had the old tree.

### Evidence

- Live run `f74e8975ae4d49a5`, ticket WS-04, was fully verified at candidate tree
  `639076e01fc6e4f430454852c77f0d6df8eefbce`, while its delivery and prepared reconciliation
  binding still named tree `69b69ca8ff487bce00c0a5675ffb4045f90636bb`.
- `_candidate_ref_for_ticket()` resolved the staged Git tree to the already verified candidate;
  there was no new semantic drift after verification.
- The old branch nevertheless selected `prepare_delivery_revalidation()` and failed closed with
  `delivery-revalidation-required changed unauthorized ticket fields` before provider mutation.
- The regression also proved that the prepared `new_head` retained the old tree, so a ledger-only
  rebind would have published a head different from the verification bundle.

### Feedback loop built

The semantic stack regression now changes the candidate during required review, completes fresh
verification, crashes once after the replacement commit and once after ledger persistence, then
resumes through two target refreshes and PR-body rebinding. It separately injects real drift after
verification and proves exactly one new bounded revalidation cycle before a second replay-safe
seal.

### Fix location and approach

`reconcile` now distinguishes three states: Git equals the delivery candidate, Git equals the
verified semantic candidate but delivery lineage is stale, or Git differs from both. The second
state commits the verified tree with a replay marker and atomically seals the new head, delivery
candidate, prepared lineage, and stale render history. The third state preserves the last delivery
binding, invalidates evidence once, and uses the same sealing transition after fresh verification.
Ledger replay validates both new transitions and rejects forged head or candidate lineage.

### Alternatives ruled out

- Weakening the existing ledger event would conceal a same-candidate invalidation.
- Editing `delivery_candidate_ref` directly would bypass crash replay and leave `new_head` stale.
- Re-running all quality stages alone would loop because the delivery comparison remained stale.
- Publishing the older prepared head would bind the PR body and merge authorization to a tree
  different from the verified candidate.

### Confidence: high

The live fail-closed state, red-green regression, commit/ledger crash matrix, real-drift cycle,
target refreshes, PR-body bundle rebind, and adversarial ledger replay all exercise the same state
boundary.
