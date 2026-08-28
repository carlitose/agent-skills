# Ticket Autopilot Reconciliation Target-Refresh Bug

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-reconciliation-target-refresh-diagnostic`
- Role: `spec`
- Standalone: true

### Children

- [RT-01 refresh a stale reconciliation target](../tickets/ticket-autopilot-reconciliation-target-refresh/done/01-refresh-stale-reconciliation-target.md)

## Type

Diagnostic spec

## Status

Fixed and covered by RT-01 regression tests.

## Diagnosis Report - lens: single-pass

### Root cause

`reconcile` durably bound `reconcile-intent.target_base.sha` before rebasing and correctly
required that exact SHA before force-with-lease push and provider retarget. When semantic
reconciliation required fresh review, QA, and verification, the base could legitimately
advance before publication. `_assert_target_base_sha()` then opened a gate, but no transition
could supersede the stale intent. Replay always checked the old SHA, while restoring remote
history was not a valid live recovery.

### Evidence

- WS-04 prepared from PR head `20b3e0e` onto `c030edb`, producing tree `4a0f23d`.
- Fresh canonical verification and finalize completed for that CandidateRef.
- LB-01 then advanced `main` to `19acf81` before publication.
- Replay stopped before provider mutation with `target base changed after reconciliation
  intent`; the old regression recovered only by forcing the test remote backwards.

### Fix

Before provider mutation, the runner now records a content-bearing refresh intent, verifies
the remote PR branch is still the old head, transplants the local reconciled patch from the
old target onto the newly observed target, and archives the superseded attempt. Semantic tree
drift creates a new CandidateRef and fresh bounded validation epoch; same-tree target movement
preserves evidence. The transition is replayable after crashes before Git mutation, after
rebase, and before ledger persistence, and it may repeat if the target advances again.

### Safety constraints

- Refresh is rejected after a reconciled push or provider retarget for the current attempt.
- Provider branch identity, force-with-lease, readback, and exact-head merge authorization
  are unchanged.
- Old/new intents, prepared refs, target SHAs, local heads, render receipts, and CandidateRefs
  remain in append-only attempt history.
- Forged attempt lineage fails ledger replay.

### Alternatives ruled out

- Restoring the remote base discards legitimate integrated work.
- Ignoring drift weakens the target-SHA guard and can publish stale work.
- Reusing evidence across a changed base tree violates CandidateRef identity.
- Manual Git or ledger repair bypasses crash replay and audit invariants.

### Confidence: high

The live run, deterministic reproduction, red-green regression, crash matrix, repeated refresh,
and ledger forgery test identify and close the same missing transition.
