---
ticket_schema: 1
ticket_id: "FS-01"
execution_mode: AFK
blocked_by: []
---

# Bind delivery branch creation to the verified base

## Artifact Graph

- Artifact ID: `artifact:fs-01-bind-delivery-branch-to-verified-base`
- Role: `ticket`
- Parent: [delivery stale-local-base diagnostic](../../specs/ticket-autopilot-delivery-stale-local-base-diagnostic.md)

## Parent Spec

[Delivery stale-local-base diagnostic](../../specs/ticket-autopilot-delivery-stale-local-base-diagnostic.md)

## What to Build

Make tracked-ticket delivery create a new branch from a commit proven to match the verified
CandidateRef base tree, instead of trusting a possibly stale local `main` ref. Preserve the
staged candidate exactly, avoid mutating user-owned base branches, and record the actual base
SHA used for delivery lineage.

## Acceptance Criteria

- [ ] A two-ticket regression advances remote `main` through the first provider merge while
      local `main` remains stale, then delivers a second candidate that edits the same file
      without opening a finalization-environment gate.
- [ ] Branch creation proves that its selected start commit has the CandidateRef base tree
      before Git mutation and preserves the exact staged and committed candidate trees.
- [ ] Delivery does not force-update, checkout, or otherwise mutate the user's local base
      branch.
- [ ] The recorded delivery lineage names the actual base commit used by branch creation and
      remains compatible with provider base-branch readback.
- [ ] Replay after branch creation and after delivery commit is idempotent.
- [ ] A missing matching base commit or genuine base-tree drift fails closed with a precise
      reconciliation requirement before push or provider mutation.
- [ ] Existing initial delivery, stacked delivery, reconciliation, ignored-source, and
      exact-head merge tests remain green.

## Frontier

Ready. The live reproduction, tree identities, source owner, and safe recovery are all pinned
in the diagnostic spec; no product or authority decision remains.

## Step-by-Step Implementation Plan

1. Add a failing long-lived stacked-delivery regression with stale local `main` and a
   same-file second candidate.
2. Move delivery branch start-point selection behind a helper that proves CandidateRef
   base-tree identity without changing the local base branch.
3. Bind delivery lineage to the selected start commit and reject unmatched or drifted bases
   before branch mutation.
4. Add replay and true-drift cases, then run focused finalizer/CLI and full runner suites.

## Testing Plan

Use deterministic temporary repositories and provider fakes. Cover stale local refs, exact
tree preservation, no local-base mutation, crash/replay boundaries, genuine drift, initial
delivery, stacked delivery, and provider readback. Run static checks and the full runner suite;
classify any exact-base failures separately.

## Out of Scope

- Reconciliation rebase policy or conflict resolution.
- Provider merge-rule discovery.
- Weakening CandidateRef, exact-head, force-with-lease, or PR-body readback guards.
- Automatically updating any user-owned local branch.
