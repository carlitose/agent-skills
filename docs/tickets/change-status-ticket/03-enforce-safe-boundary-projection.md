---
ticket_schema: 1
ticket_id: "CST-03"
execution_mode: AFK
blocked_by:
  - "CST-01"
  - "CST-02"
---

# Enforce mutation barriers and safe-boundary projection

## Artifact Graph

- Artifact ID: `artifact:cst-03-safe-boundary-status-projection`
- Role: `ticket`
- Parent: [Change Status Ticket](../../specs/change-status-ticket.md)

## Parent Spec

[Change Status Ticket](../../specs/change-status-ticket.md)

## What to Build

Make the repository lifecycle intent authoritative at every runner mutation boundary and add append-only disposition projection for active, gated, and waiting attempts after an exact atomic safe boundary. Preserve candidates, checkpoints, provider observations, gates, waits, stop reasons, and historical evidence; prohibit new work after the barrier; and project only from ignored-source readback or tracked terminal truth rather than a stale run worktree.

## Acceptance Criteria

- [ ] Every implementation, Git, provider, delivery, merge, reconciliation, completion, wiki, and Pi mutation boundary checks an exact repository lifecycle intent under repository/run locks.
- [ ] An in-flight atomic effect settles and is read back truthfully before the barrier; interruption or uncertain outcome gates.
- [ ] Active work receives one append-only stopped-at-safe-boundary receipt with non-empty reason; candidate, checkpoints, evidence, PR, and external-effect receipts remain literal history.
- [ ] Gated and waiting attempts preserve their exact gate/wait evidence and become administratively unschedulable without treating a gate as user or merge authority.
- [ ] Pending, active, gated, waiting, verified, PR-open/delivery, integrated, and completed states have an explicit tested matrix; integrated/completed transitions reject and uncertain delivery states gate.
- [ ] A usable run projection validates repository transaction identity and terminal/ignored source truth, not the stale run worktree path; missing and retired runs need no rewrite.
- [ ] Hold/cancel never cascades to dependents; readiness is recomputed with existing held/canceled dependency reasons.
- [ ] Reopen consumes one passed ticket-bound human gate, creates pending work, invalidates current candidate-through-merge authority, and preserves old evidence only as history.
- [ ] Barrier/projection crash replay is single-shot and contradictory intent, source, gate, receipt, or projection fails closed.
- [ ] Existing schema-4 ledgers are extended versionedly; legacy/retired ledgers and current run-bound lifecycle commands are not silently migrated.
- [ ] Concurrency tests prove an active runner cannot begin a new mutation after the barrier is durable.
- [ ] No real ticket status, provider object, worktree cleanup, wiki, or Pi operation is verification evidence.

## Frontier

Dependency-blocked by CST-01 and CST-02. It remains AFK only because concurrency, provider, and state evidence must use disposable fixtures; any real status action requires separate user authority.

## Step-by-Step Implementation Plan

1. Define the repository-intent lookup and immediate mutation-boundary guard.
2. Add lock ordering and safe-boundary receipts for active and settled gated/waiting attempts.
3. Implement terminal/ignored source-bound run projection and exact replay.
4. Extend reopen invalidation and readiness/no-cascade behavior without reusing authority.
5. Add concurrent runner, in-flight effect, stale worktree, crash, and contradiction fixtures.

## Testing Plan

Use concurrent disposable processes or deterministic lock fixtures across every mutation seam. Inject provider and Git outcomes around the barrier, preserve exact candidate/evidence snapshots, and exercise the full state matrix plus dependencies and reopen. Verify no post-barrier effect begins.

## Out of Scope

- Public skill/routing changes.
- New lifecycle vocabulary or cancellation cascade.
- Provider merge without separate authority.
- Real disposition, provider publication, issue close/reopen, wiki, Pi-sync, or cleanup.
