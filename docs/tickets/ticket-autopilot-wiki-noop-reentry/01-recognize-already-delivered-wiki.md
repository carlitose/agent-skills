---
ticket_schema: 1
ticket_id: "WNOP-01"
execution_mode: AFK
blocked_by: []
---

# Recognize an already-delivered wiki and recover its exact failure

## Artifact Graph
- Artifact ID: `ticket:ticket-autopilot-wiki-noop-reentry:WNOP-01`
- Role: ticket
- Parent: [Wiki no-op reentry](../../specs/ticket-autopilot-wiki-noop-reentry.md)

## Parent Spec
[Tracked wiki already-at-target delivery and exact reentry](../../specs/ticket-autopilot-wiki-noop-reentry.md).

## What to Build
Recognize an exact frozen wiki already present on the current delivery base as a validated no-op, complete the post-integration wiki effect idempotently, and add narrowly scoped recovery for the historical terminal no-Git-diff failure.

## Acceptance Criteria
- [ ] Exact already-present content yields a head/tree/candidate-bound no-op after fresh base readback, without a new commit, branch, PR, provider call or merge authorization; the protected checkout stays untouched.
- [ ] Post-integration completion is durable and repeated resume is idempotent, without claiming a new merge or transferring application verification.
- [ ] Existing retry CLI accepts only the exact integrated pre-provider no-diff failure with intact candidate and matching persisted target receipt; failed-record digest and actor/evidence bind preparation, full predecessor retention, interrupted replay and readback. Preparation remains provider-free.
- [ ] Git errors, invalid content/modes/target/receipt, base movement during no-op materialization, stale digest and prior provider/authorization evidence cannot become success. Existing non-empty delivery and historical exact retry guards remain intact.
- [ ] Operational reference documents the successful no-op and exact recovery, with focused RED/GREEN and negative-path evidence on the frozen candidate; no installed runner or BetShareMarket ledger is patched.

## Frontier
Ready. The user authorized this follow-up after BetShareMarket PR #297 integrated and its wiki hit the no-diff terminal failure. Existing repository merge authority is separate from this ticket's wiki delivery grant.

## Step-by-Step Implementation Plan
1. Reproduce no-diff delivery and retry rejection using disposable Git/frozen-candidate fixtures.
2. Implement exact no-op recognition and driver completion, preserving non-empty delivery and target/file validation.
3. Extend only the historical no-diff retry shape, validating its persisted target and preserving existing provenance/replay protocol.
4. Run focused causal and negative tests, simplify, review, plan/execute QA, and validate the frozen Verification Record.
5. Deliver through the runner, then separately validate/deliver its wiki before bundle alignment and consumer recovery.

## Testing Plan
Focused unittest entrypoints for wiki no-op, driver/retry, byte fidelity and target validation. Use real temporary Git repositories and fake provider command transports; no live provider mutation inside tests. Announce any broader checks and retain timeout/platform limitations rather than rerunning long suites per change.

## Scope
`ticket-autopilot/scripts/autopilot/wiki_sync.py`, directly related wiki tests, and `ticket-autopilot/references/wiki-delivery.md`. Tracked spec/ticket completion effects belong to the runner.

## Out of Scope
Direct consumer-ledger edits, generic reset/force recovery, fabricated empty commits/PRs, unrelated terminal failures, normal merge-policy changes, package installation or Pi reload, bookmaker/LLM traffic, credentials/deployment/DNS, and broad timeout investigation.
