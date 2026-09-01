---
ticket_schema: 1
ticket_id: "RDR-02"
execution_mode: AFK
blocked_by: []
---

# Prioritize explicit reconciliation over pending merge

## Artifact Graph

- Artifact ID: `artifact:rdr-02-prioritize-explicit-reconciliation`
- Role: `ticket`
- Parent: [Ticket Autopilot Runner Defect Remediation](../../specs/ticket-autopilot-runner-defect-remediation.md)

## Parent Spec

[Ticket Autopilot Runner Defect Remediation](../../specs/ticket-autopilot-runner-defect-remediation.md)

## What to Build

Fix GitHub issue [#201](https://github.com/carlitose/agent-skills/issues/201). In one `resume` call, a validated caller-supplied `reconcile` event for the pending ticket must run before automatic pending-merge dispatch. Recompute merge readiness only after the explicit event persists.

## Acceptance Criteria

- [ ] A focused ordering regression fails on the current baseline with one pending authorized merge plus one explicit reconciliation event and observes the merge path before reconciliation.
- [ ] Resume validates/inspects the exact event batch before using it for priority; malformed, stale, or incomplete events cannot silently suppress pending merge.
- [ ] An explicit reconciliation for the pending ticket executes first and records zero old-head provider merge mutation before the reconciliation result.
- [ ] After event persistence, pending merge eligibility is derived again from current ledger state; a new exact eligible head may proceed, while revalidation-required or gated reconciliation cannot merge the obsolete head.
- [ ] Event batches without the relevant explicit reconciliation preserve current pending-merge ordering and replay semantics.
- [ ] Repository-authorized derived reconciliation, caller events, autonomous merge, provider gates, pause, and crash/replay regressions pass.

## Frontier

Ready. `_resume()` on the current baseline invokes `_drive_pending_merge()` before `_process_events()`.

## Step-by-Step Implementation Plan

1. Add a deterministic fake-provider resume test that records operation order and old-head mutation count.
2. Introduce a bounded validated event-batch inspection or processing seam without a second competing event parser.
3. Process the relevant explicit reconciliation before pending merge and re-derive readiness afterward.
4. Add malformed, unrelated-event, gated, revalidation-required, and replay controls.
5. Run focused/full CLI and reconciliation suites, compilation, exact diff/tree checks, and Artifact Graph delta.

## Testing Plan

Use the public `resume` path with a real event file, fake provider receipts, and a merge mutation spy. Assert ordering, persisted ledger state, expected head, event replay, and no bypass of reconciliation or merge authority.

## Out of Scope

- Giving every explicit event priority over pending merge.
- Manufacturing reconciliation authority or accepting caller semantic-equivalence claims.
- Changing `merge-all` policy except where it delegates to the corrected shared resume ordering.
