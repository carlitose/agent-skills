---
ticket_schema: 1
ticket_id: "PRT-01"
execution_mode: AFK
blocked_by: []
---

# Refresh a conflict-blocked reconciliation intent before prepare

## Artifact Graph

- Artifact ID: `artifact:prt-01-refresh-conflict-blocked-intent-before-prepare`
- Role: `ticket`
- Parent: [Ticket Autopilot Pre-prepare Reconciliation Target Refresh](../../specs/ticket-autopilot-preprepare-reconciliation-target-refresh.md)

## Parent Spec

[Ticket Autopilot Pre-prepare Reconciliation Target Refresh](../../specs/ticket-autopilot-preprepare-reconciliation-target-refresh.md)

## What to Build

Add a crash-safe pre-prepare target-refresh transaction for an initial reconciliation intent
that persisted before a real conflict. Permit only exact target SHA/tree advancement, retain
all old and superseded pending intents, apply the existing authorized proposal against the
newest target, and install the replacement only with exact `reconcile-prepare` readback.

## Acceptance Criteria

- [ ] A conflict-blocked intent without `reconcile-prepare` can refresh only target SHA/tree
      and reach the exact proposal resolver.
- [ ] Target branch/ref, old/local/remote head, parent, source, run, ticket, grant, and every
      non-target intent field remain exact and fail closed on drift.
- [ ] Old intent and repeated pending refreshes are append-only, persisted before Git, and
      consumed exactly once only when prepare is created.
- [ ] An exact proposal against the newest target records adoption/application, consumes only
      covered gates, and triggers normal fresh CandidateRef quality.
- [ ] Crash/replay before Git, after proposal application, and around prepare installation is
      idempotent without provider mutation or lost history.
- [ ] Existing prepared-candidate refresh, provider, merge, completion, publication, wiki,
      Pi, source, and cleanup authority contracts remain unchanged.
- [ ] Full regressions, forward scenarios, static/context checks, and Artifact Graph delta
      pass with no stronger live-provider claim.

## Frontier

Ready. No human decision or provider mutation is required. RD-04 remains gated and must not
be manually rewritten while this runner correction is delivered.

## Step-by-Step Implementation Plan

1. Add exact target-only intent delta validation and fail-closed pending-refresh state.
2. Persist initial refresh and repeated-replacement history before worktree mutation.
3. Extend kernel prepare to atomically archive the old intent, install the replacement, and
   consume pending state exactly once.
4. Add disposable real-Git conflict/proposal/crash coverage plus strict negative tests.
5. Run focused/full regressions, extension/forward, context/static, and Artifact Graph checks.

## Testing Plan

Use real disposable repositories/remotes and the production reconciliation proposal path.
Exercise one and repeated target advances, non-target drift, revoked/malformed authority,
conflict persistence, exact application, prepare consumption, crash replay, and provider
mutation guards. No live provider action is needed.

## Out of Scope

- Manual RD-04 intent, branch, gate, or ledger mutation.
- Semantic conflict resolution without the exact proposal.
- Live issue publication or RD-05 authorization.
- Post-provider-mutation target refresh.
