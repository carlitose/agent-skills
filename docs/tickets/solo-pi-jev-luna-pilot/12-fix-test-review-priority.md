---
ticket_schema: 1
ticket_id: "SPB-12"
execution_mode: AFK
blocked_by:
  - "SPB-10"
---

# SPB-12 — Test fallito non bloccato da review-format

## Artifact Graph
- Artifact ID: `artifact:solo-pi-jev-spb-12`
- Role: `ticket`
- Parent: [Test failure priority](../../specs/solo-pi-jev-test-failure-priority.md)

## Parent Spec
[Test failure priority](../../specs/solo-pi-jev-test-failure-priority.md).

## What to Build
Minimal precedence repair: known public failure reaches bounded fix even with unparsed review;
green-test unparsed review still gates. Clarify concrete-file review format without parser change.

## Acceptance Criteria
- [ ] Known failed public test + unparsed review reaches quality failure/fix, preserves receipts/prose/partial findings and no external approval.
- [ ] Green tests + unparsed review still gates0; capture/readonly and ordinary blocker/NO/uncertainty/quality3 remain unchanged.
- [ ] Role instructions require concrete relative file marker; no parser, threshold, hidden/product intervention or historical mutations.
- [ ] Causal RED/GREEN and frozen controller/repair contrasts with substituted ports, inline review/QA/audit and handoff; no live calls in repair.

## Frontier
Ready: SPB-10 complete; SPB-11 real gated cell r4 is causal evidence, not completed dependency.
Current explicit repair-loop mandate covers local repair/retest.

## Step-by-Step Implementation Plan
1. Canonical admission and causal failing test.
2. Minimal conditional/prompt change, targeted regression and frozen quality/handoff.
3. Subsequent distinct live trial retains all prior budget/history.

## Testing Plan
Actual Git/public process and fake peer/semantic ports; failed-versus-green review-format contrast,
controller/repair regressions. No Budget or model suite replay.

## Out of Scope
Parser expansion, review relabel/auto-approval, question/policy/quality limit changes, product
intervention, historical/source/ledger reset, live launches inside repair, delegation/runner,
commit/push/PR/merge/install/reload/wiki sync.
