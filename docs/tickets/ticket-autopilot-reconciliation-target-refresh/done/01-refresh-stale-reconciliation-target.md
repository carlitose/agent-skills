---
ticket_schema: 1
ticket_id: "RT-01"
execution_mode: AFK
blocked_by: []
---

# Refresh a stale reconciliation target

## Artifact Graph

- Artifact ID: `artifact:rt-01-refresh-stale-reconciliation-target`
- Role: `ticket`
- Parent: [reconciliation target-refresh diagnostic](../../../specs/ticket-autopilot-reconciliation-target-refresh-diagnostic.md)

## What Was Built

Ticket Autopilot can now refresh a reconciliation target that advances during required
revalidation. It records the refresh before Git mutation, archives each superseded attempt,
replays safely across crash points, and never weakens provider or exact-head guards.

## Acceptance Criteria

- [x] The end-to-end semantic regression advances the target twice without restoring remote
      history and reaches reconciled provider readback.
- [x] Refresh requires an unchanged provider branch and is forbidden after reconciled push or
      retarget state.
- [x] Refresh intent precedes local mutation and archived attempts retain old/new target,
      intent, prepared CandidateRef, head, and render lineage.
- [x] Semantic target changes derive a new CandidateRef and invalidate review, QA,
      verification, PR-body binding, and merge authorization.
- [x] Crashes before mutation, after rebase, and before prepared-ledger persistence resume
      idempotently.
- [x] A second target advancement repeats the same bounded cycle.
- [x] Final publication keeps force-with-lease, provider retarget/readback, and exact-head
      requirements.
- [x] Same-tree refresh preserves evidence and existing provider-race gates still pass.
- [x] Ledger replay rejects forged refresh lineage.
- [x] Focused CLI, kernel, semantic-candidate, and replay suites pass.

## Testing

- Semantic target-refresh/rebind regression: pass, including three crash points and two
  consecutive semantic refreshes.
- Existing crash-resumable delivery regression: pass with same-tree evidence preservation and
  provider-retarget race coverage.
- Kernel plus semantic CandidateRef suites: 81 tests passed.
- Full CLI suite: 59 tests passed.

## Out of Scope

- Automatic rebase-conflict resolution.
- Refresh after provider mutation for the current attempt.
- Evidence reuse after semantic tree drift.
- Changes to merge policy or provider authorization.
