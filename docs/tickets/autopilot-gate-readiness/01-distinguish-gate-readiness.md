---
ticket_schema: 1
ticket_id: "RGC-01"
execution_mode: AFK
blocked_by: []
---

# Distinguish technical gates and reuse exact existing authority

## Artifact Graph
- Artifact ID: `artifact:autopilot-gate-readiness-rgc-01`
- Role: `ticket`
- Parent: [Gate readiness spec](../../specs/autopilot-gate-readiness.md)

## Parent Spec
[Gate readiness spec](../../specs/autopilot-gate-readiness.md), especially Decision, Invariants and External behavior.

## What to Build
Correct the runtime status projection that labels every gate as human, and provide the matching scoped operator procedure. Preserve the existing resolution mechanism and every historical gate. This is not an automatic recovery or authorization feature.

## Acceptance Criteria
- [ ] All open gate IDs have an accurately named accessor; the human accessor filters only persisted human-category gates.
- [ ] Applicable human gates yield `human-gated`, environment-only gates yield `environment-gated`, and other/mixed/unavailable classifications yield conservative `gated`; human takes precedence in mixed sets.
- [ ] Status retains all open gates/records in order and remains pure; barriers, dependencies and unrelated AFK readiness are unchanged.
- [ ] Owning guidance requires exact current cause, prerequisite evidence and original implementation/recovery scope before using the existing resolution path. It reuses a valid existing decision rather than demanding a duplicate prompt, without treating merge authority or category labels as recovery permission.
- [ ] Resolution regression proves recorded-stage reentry, unchanged uncompleted quality state and unrelated human gates. No fixture is called live authorization evidence.
- [ ] Historical generic reasons, ledger bytes and quality/provenance remain unchanged by reporting; no approval, migration or ledger-repair side effect is added.
- [ ] Documentation explains the new readiness values and intentionally corrected Python accessor semantics, with all stated non-goals intact.

## Frontier
Ready AFK. The user requested the runner correction and normal delivery. No subagents; compose review and QA inline and report shared context honestly. No new user decision is needed to correct this demonstrated projection bug. Any genuine runtime gate remains separate.

## Step-by-Step Implementation Plan
1. Reproduce the environment/human conflation on the clean base using disposable kernel fixtures; retain the observed result.
2. Correct accessors and readiness classification together; inspect every caller so public open-gate visibility never shrinks.
3. Add/update the owning operator procedure and status contract without adding a second authority or recovery system.
4. Add causal category, scope, ordering, replay, no-write and stage-reentry regressions; keep unrelated ready work and human decisions protected.
5. Simplify the candidate, then perform fresh review, causal QA, canonical verification and normal provider-gated delivery on the final CandidateRef.

## Testing Plan
- Kernel and CLI/status fixtures for environment versus human, mixed/run-scoped/closed/other gates, all-gate enumeration and unchanged scheduler behavior.
- Existing missing-reason, generic-reason replay, source/projection recovery and human-start/reopen regressions.
- Operator-guidance review for valid prior scope, merge-only scope, restored versus unattempted prerequisites, stale candidates and real human decisions.
- Focused documentation/static graph checks and selected forward scenarios; broader local tests only with explicit outcomes and finite bounds.
- No live BetShareMarket mutation, independent-review, full-suite, provider readiness, wiki merge, package installation or active Pi reload claim.

## Out of Scope
- New gate states, ledger migrations, technical-recovery commands, automatic approvals or grant stores.
- Structured stop-evidence validation and the Pi continuation/compaction adapter; these remain separate planned work.
- SW-06 historical decisions; completion provenance repairs already integrated; Windows Pi launcher implementation.
- Any edits to the original dirty checkout, installed package, real historical ledger or unrelated source.
