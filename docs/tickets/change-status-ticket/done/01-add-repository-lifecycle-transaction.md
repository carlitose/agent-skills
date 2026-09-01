---
ticket_schema: 1
ticket_id: "CST-01"
execution_mode: AFK
blocked_by: []
---

# Add the repository lifecycle transaction and ignored-source slice

## Artifact Graph

- Artifact ID: `artifact:cst-01-repository-lifecycle-transaction`
- Role: `ticket`
- Parent: [Change Status Ticket](../../specs/change-status-ticket.md)

## Parent Spec

[Change Status Ticket](../../specs/change-status-ticket.md)

## What to Build

Add a versioned repository-common lifecycle transaction that resolves one exact ticket and optional usable-run projection without making a run own the operation. Deliver the first vertical slice for pending ignored sources: validate exact administrative vocabulary and user authority, persist intent before the existing source primitive, recover exact receipts, read back the source, and report `external-unpublished`. For tracked sources, stop after a durable handoff to CST-02; for active, gated, waiting, or delivery states, emit the exact safe-boundary gate rather than using the current run worktree.

## Acceptance Criteria

- [ ] Repository identity, Git common-directory identity, ticket Artifact ID/path/digest, prior and target dispositions, actor, reason, authority reference, source mode, target branch/SHA, and reopen gate form one canonical transaction identity.
- [ ] Only `open`, `on-hold`, and `canceled` are accepted; lifecycle/readiness/stop/completion values fail before effects.
- [ ] Hold/cancel require direct actor, reason, and durable authority; reopen consumes one exact ticket-bound passed human gate and rejects caller drift.
- [ ] One matching usable schema-4 run is only a projection target; missing and retired ownership proceed; multiple usable owners or source contradictions gate.
- [ ] The transaction journal is versioned, append-only, lock-protected, secret-safe, and exact-replayable; unknown or contradictory schemas fail closed.
- [ ] Pending ignored-source hold/cancel/reopen uses the existing transition primitive, recovers before/after-move crashes, and returns `external-unpublished` with no Git/provider/merge/terminal/tracked-completion/wiki/Pi effect.
- [ ] Tracked sources persist a source-ready handoff but perform no target-run staging or provider mutation in this ticket.
- [ ] Active, gated, waiting, PR-open/delivery, completed, in-flight atomic, and ambiguous ownership states return stable named gates without mutating source or run state.
- [ ] Existing run-bound lifecycle commands and historical receipts retain their literal behavior; compatibility is opt-in.
- [ ] No real project ticket or live provider object is used as test evidence.

## Frontier

Ready for AFK implementation. No real disposition or provider authority is required because all mutation evidence uses disposable fixtures.

## Step-by-Step Implementation Plan

1. Define the repository transaction schema, canonical identity, storage path, locks, and fail-closed loader.
2. Build exact repository/ticket/source/run resolution and normalized authority validation.
3. Compose the existing transition primitive for ignored pending-source fixtures only.
4. Add phase/readback reporting, exact replay, and tracked/non-pending handoff gates.
5. Cover duplicate IDs, source drift, schema contradiction, crash boundaries, and all non-authorities with disposable fixtures.

## Testing Plan

Use temporary tracked and ignored repositories plus schema-4/retired/missing/ambiguous ledger fixtures. Inject crashes before intent, before source move, and after move before applied receipt. Assert no Git/provider operation for ignored mode and no real repository mutation.

## Out of Scope

- Tracked commit, push, PR, merge, terminal proof, or projection.
- Active/gated/waiting mutation barriers or state projection.
- Public skill or routing changes.
- Real disposition, publication, wiki, Pi-sync, cleanup, or target-ticket implementation.
