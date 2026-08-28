---
ticket_schema: 1
ticket_id: "VR-01"
execution_mode: AFK
blocked_by: []
---

# Rebind a verified reconciliation candidate

## Artifact Graph

- Artifact ID: `artifact:vr-01-rebind-verified-reconciliation-candidate`
- Role: `ticket`
- Parent: [verified reconciliation delivery-rebind diagnostic](../../../specs/ticket-autopilot-verified-reconciliation-delivery-rebind-diagnostic.md)

## What Was Built

Reconciliation resume now seals a corrected, fully verified candidate into a replay-safe commit
and updates its delivery candidate, prepared head, semantic lineage, and stale render history in
one audited transition. Genuine post-verification drift keeps the last delivery binding, runs one
fresh bounded quality epoch, and then uses the same seal before publication.

## Acceptance Criteria

- [x] The semantic stack regression reproduces a verified candidate that differs from stale
      delivery and prepared lineage.
- [x] Sealing preserves CandidateRef, artifact generation, leaf results, verification checkpoints,
      and validated stages while clearing one-shot merge authority.
- [x] The replacement commit and ledger transition replay after crashes on either side of durable
      ledger persistence.
- [x] Reconciled PR-body rendering binds the current verification bundle and head while retaining
      append-only body and reconciliation history.
- [x] Genuine Git drift from both semantic and delivery candidates invalidates evidence exactly
      once, preserves the previous delivery binding, and seals only after fresh verification.
- [x] Same-tree reconciliation, repeated target refresh, provider-race, and existing PR-body
      rebind behavior remain covered.
- [x] Ledger replay rejects forged seal head lineage and unrelated mutations.
- [x] Focused CLI, kernel, replay, compilation, and patch-integrity checks pass; full-suite
      baseline differences are reported explicitly.

## Testing

- Semantic reconciliation/rebind regression: pass, including two seal crash points, genuine
  post-verification drift, two target refreshes, and fresh-bundle PR-body publication.
- Existing equivalent reconciliation and crash-resumable delivery regressions: pass.
- Kernel and semantic replay suites: pass.
- Full runner suite: 445 of 448 passed; the three `wait-what` inventory-policy failures
  reproduced unchanged on `main`.
- Python compilation and `git diff --check`: pass.

## Out of Scope

- Automatic rebase-conflict resolution.
- Weakening force-with-lease, provider readback, exact-head merge, or append-only audit guards.
- Manual production-ledger repair.
- Unrelated baseline failures outside Ticket Autopilot reconciliation.
