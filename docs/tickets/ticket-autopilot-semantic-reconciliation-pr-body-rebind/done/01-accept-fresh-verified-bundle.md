---
ticket_schema: 1
ticket_id: "RB-01"
execution_mode: AFK
blocked_by: []
---

# Accept a fresh verified bundle after semantic reconciliation

## Artifact Graph

- Artifact ID: `artifact:rb-01-accept-fresh-verified-bundle`
- Role: `ticket`
- Parent: [semantic reconciliation PR-body rebind diagnostic](../../../specs/ticket-autopilot-semantic-reconciliation-pr-body-rebind-diagnostic.md)

## Parent Spec

[semantic reconciliation PR-body rebind diagnostic](../../../specs/ticket-autopilot-semantic-reconciliation-pr-body-rebind-diagnostic.md)

## What to Build

Fix ticket-autopilot's semantic-reconciliation PR-body rebind so a newly verified CandidateRef
can persist its fresh verification bundle without weakening append-only receipt lineage. Use
the confirmed root cause and constraints in the parent diagnostic.

## Acceptance Criteria

- [x] A full regression reproduces `delivery-recorded PR-body rebind is not append-only` on
      the pre-fix path: open stacked PR, semantic reconciliation, fresh CandidateRef, fresh
      verification, and PR-body render.
- [x] The same scenario persists a schema-2 PR-body receipt and reaches provider readback
      after the fix.
- [x] The current render request and receipt bind the fresh bundle to the current CandidateRef
      and verified handoff; a forged or stale bundle fails closed.
- [x] Append-only lineage retains the complete old receipt and closes over old/new head, body,
      request, and bundle identities. Missing lineage, mutation, or schema downgrade fails.
- [x] Lineage-equivalent reconciliation preserves its current evidence and same-bundle
      behavior without consuming new quality work.
- [x] Crash-before-save and exact replay remain idempotent, and no test forces or patches a
      ledger outside the public kernel/finalizer transition.
- [x] Focused ledger, finalizer, semantic-candidate, and CLI tests pass; the full
      ticket-autopilot suite reports no candidate regression.

## Frontier

Complete. The runner accepts a fresh verified bundle after semantic reconciliation while
preserving append-only receipt lineage and exact-head delivery safety.

## Step-by-Step Implementation Plan

1. Add the end-to-end failing test at the semantic-reconciliation render boundary.
2. Bind the current validated bundle identity into the reconciliation render request and
   schema-2 lineage closure.
3. Update `_pr_body_rebind_is_closed()` to accept the fresh bound bundle while preserving all
   old-receipt, request, head, body, CandidateRef, and downgrade checks.
4. Add forged/stale bundle, lineage tamper, crash, replay, equivalent-reconciliation, and
   legacy-request migration counterexamples.
5. Run focused and full ticket-autopilot suites and record only observed evidence.

## Testing Evidence

- The semantic CLI regression uses real local Git repositories and a stateful simulated GitHub
  provider to reach retarget/readback after fresh verification.
- The equivalent-reconciliation CLI regression remains green without consuming new leaf work.
- Focused kernel, finalizer, semantic-candidate, verification, provider-body, forward-matrix,
  and CLI coverage is green.
- The full suite reports 434 passes. Its only three failures are the pre-existing `wait-what`
  inventory/policy baseline failures, reproduced unchanged on the unmodified branch.

## Out of Scope

- Changing Model Eval, Groq, deployment, or project code.
- Weakening candidate invalidation, verification bundle validation, exact-head authorization,
  or provider readback.
- Repairing affected ledgers by hand or adding a bypass for the audit.
- Redesigning PR bodies or stack reconciliation beyond the fresh-bundle closure defect.
