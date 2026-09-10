---
ticket_schema: 1
ticket_id: "CPR-01"
execution_mode: AFK
blocked_by: []
---

# Preserve completion provenance during candidate correction

## Artifact Graph
- Artifact ID: `artifact:ticket-autopilot-completion-provenance-cpr-01`
- Role: `ticket`
- Parent: [Completion provenance](../../specs/ticket-autopilot-completion-provenance.md)

## Parent Spec
[Preserve completion provenance across final-candidate corrections](../../specs/ticket-autopilot-completion-provenance.md)

## What to Build
Implement the spec's corrected-candidate finalization boundary: consume receipt-derived completion state rather than a report-only field, and validate an ordinary tracked completion summary against its first immutable candidate-bound effect receipt. Reuse existing history, preserve no-clobber behavior, and leave authorization and fresh-quality rules unchanged.

## Acceptance Criteria
- [ ] A fully completed enabled projection does not replay before a staged correction; D2 enters implementation with all previous quality invalidated and history retained.
- [ ] Genuine interrupted or contradictory projection retains exact recovery and fail-closed behavior.
- [ ] Ordinary tracked I completion → D review failure → correction → fresh D2 quality → guarded delivery preserves the original summary byte-for-byte.
- [ ] Replay uses the first completion identity, not the newest candidate or a later replay receipt. Missing, corrupt, mismatched, or symlinked summary/provenance fails without replacement or provider mutation.
- [ ] Existing projection provenance, source ownership, post-provider restrictions, ledger schema/history, quality and merge gates remain intact.
- [ ] Focused real-Git CLI tests, unit negatives, relevant broader/forward checks and final-candidate review/QA/verification pass with explicit local-evidence ceilings; failures and timeouts are preserved.
- [ ] SW-04 and WBF-01 evidence remains untouched; no recovery or deployment is claimed by this ticket.

## Frontier
Ready AFK; no ticket dependencies or human decision needed for this deterministic repair. Existing affected-run gates remain separate and unchanged. The user's ongoing request authorizes implementation inline, not delegation or invented gate approval.

## Step-by-Step Implementation Plan
1. Reproduce completed-projection correction and ordinary summary replay in disposable fixtures; record RED evidence.
2. Share the persisted-receipt completion-state query between report and recovery; retain interrupted-transaction handling.
3. Reuse original summary-effect provenance in ordinary tracked replay, requiring exact document identity and first-effect binding; preserve no-clobber and all delivery guards.
4. Add replay, tamper/missing/symlink and post-provider negatives; simplify the shared boundary without unrelated refactoring.
5. Run focused and broader checks, then fresh review, QA, verification and standard delivery for the final CandidateRef.

## Testing Plan
Real-Git CLI tests for I→D projection, interrupted recovery and D2 adoption; ordinary finalization through D2 with original summary preserved; no provider calls before qualified delivery. Unit checks for first-event selection and exact effect-key binding, run/ticket/digest/snapshot contradictions, missing/corrupt files/receipts and repeated replay. Include final-tree, finalizer, kernel, ledger and relevant forward scenarios. Read-only checks preserve the two affected live ledgers and WBF summary. Shared-context review is not independent; local fake-provider tests do not prove live provider behavior.

## Out of Scope
- Implementing or resuming SW-04, WBF-01, SW-06 or wiki delivery within this ticket.
- Manual ledger/index/receipt repair, historical backfill, new authority, gate relaxation or a parallel provenance store.
- General ignored-source redesign, arbitrary reconciliation, delegation, local Pi installation or reload.
