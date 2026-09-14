---
ticket_schema: 1
ticket_id: "PMV-01"
execution_mode: AFK
blocked_by: []
---

# PMV-01 — Verify merged source without reopening delivery

## Artifact Graph
- Artifact ID: `ticket:postmerge-verification-reentry:PMV-01`
- Role: `ticket`
- Parent: [Post-merge verification reentry](../../specs/ticket-autopilot-post-merge-verification-reentry.md)

## Parent Spec
[Post-merge verification reentry](../../specs/ticket-autopilot-post-merge-verification-reentry.md)

## What to Build
Implement the complete gate-scoped post-merge verification session specified by the parent:
normal exact-source CandidateRef/context binding, fresh bounded quality, canonical audit and
condition-only completion, with public CLI/event access and atomic ledger persistence. Keep
the integrated predecessor and unstarted successor separate from this quality session.

Own the session invariant as one change across `ticket-autopilot/scripts/autopilot`, focused
runner tests, the forward scenario and a short operator reference. Reuse canonical ticket,
CandidateRef, leaf and verification contracts. Do not import unrelated installed/local patches.

## Acceptance Criteria
- [ ] AC1: A public provider-free path binds an exact clean registered merged source to the
  normalized integrated predecessor and technical gate, emits a runner CandidateRef/context,
  and leaves both ticket lifecycles and the release barrier unchanged during verification.
- [ ] AC2: Wrong repository, source/head/tree, replacement refs, dirt, ambiguous predecessor,
  malformed or unrelated gate, held/canceled/paused scope and contradictory prerequisites
  fail before mutation; the actual gated/null-candidate dead end is reproduced causally.
- [ ] AC3: Existing schema-3 phases, isolation, artifact bindings and configured budgets apply
  to fresh review, QA plan/execution and verification. Old/cross-ticket/out-of-order results,
  partial-as-complete and false independence cannot become passes; replay does not reset budget.
- [ ] AC4: The canonical Verification Audit validator/reducer and exact stage/criteria/source
  bindings determine completion. Tampering, stale/unknown evidence and human approval alone
  cannot resolve the condition. Valid proof resolves only the technical gate and grants no
  canary, deployment, production or merge authority.
- [ ] AC5: Locked persisted round trips, interruption/replay and history validation preserve
  old schema-4 history, the historical predecessor, the unstarted successor and other gates.
  Status is pure, and ignored/tracked ticket/source behavior outside this lane does not regress.
- [ ] AC6: Focused and full runner/verification tests, forward scenarios, static, context-budget
  and Artifact Graph delta checks pass or report exact environment limitations. No fixture
  result is called live evidence; public documentation explains invocation and claim limits.
- [ ] AC7: Produce a validated normal delivery handoff. Consumer replay and personal-config
  alignment remain post-integration operations; neither the installed runner nor consumer
  ledger is edited directly, and unrelated working files remain unchanged.

## Frontier
Ready AFK. The user explicitly authorized this bounded cross-repository correction and its
subsequent merge. Run serially inline. No implementation decision requires a new human gate;
real quality/provider/environment limitations remain visible. The consumer's live approvals
remain separate and ungranted.

## Step-by-Step Implementation Plan
1. Reproduce the gated/null-candidate failure with canonical fixtures and real Git objects;
   pin the intended source/session/parent identities and lifecycle preservation assertions.
2. Implement the gate-scoped contract with narrow source and ledger adapters, reusing the
   canonical budget/leaf/audit owners. Add explicit history validation and no-effect negatives.
3. Exercise the complete public persisted quality/replay path and condition-only resolution.
4. Add focused operator guidance and forward coverage, simplify without changing scope, then
   perform disclosed inline review, causal QA and canonical verification on the frozen candidate.
5. Return normal finalization/merge handoff; align the consuming configuration only after the
   runner's durable integration and required separate config delivery.

## Testing Plan
- Real temporary Git objects, canonical tickets, ledgers and artifact hashes for integration.
- Public entry/status/result commands and actual canonical audit validation in positive cases.
- Independent negative predicates for identity, lifecycle, evidence, order, replay and budgets.
- Fail-on-call sentinels for provider/deployment/install effects; no fake successful live calls.
- Full Ticket Autopilot, verification-audit, forward/static/context-budget and graph regressions.
- Post-integration consumer replay only within its still-valid original authority; no SSH or
  WilliamHill exception is reissued by this ticket.

## Out of Scope
- Reopening/completing the consumer's delivery tickets or changing their historical CandidateRefs.
- Gate bypass, hand-edited ledgers, installed-code hotfixes, historical-pass promotion or new
  ad hoc approval/security systems.
- Provider mutation by the new verification path, canary/deploy/DNS, live credentials or traffic.
- Unrelated local repairs, broad dependency updates, active Pi reload, or wiki candidate merging.
