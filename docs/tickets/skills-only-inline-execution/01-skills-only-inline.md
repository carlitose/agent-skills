---
ticket_schema: 1
ticket_id: "SH-01"
execution_mode: AFK
blocked_by: []
---

# SH-01 — Support skills-only inline execution

## Artifact Graph
- Artifact ID: `artifact:skills-only-inline-execution-sh01`
- Role: `ticket`
- Parent: [Skills-only inline execution](../../specs/skills-only-inline-execution.md)

## Parent Spec
[Skills-only inline execution](../../specs/skills-only-inline-execution.md)

## What to Build
Repair the mandatory policy and connected skill inputs so an explicitly selected skills-only
lane can compose execute-ticket inline without a runner, scheduler, substitute driver, or
settings reset. Preserve canonical quality contracts and real delivery authority.

## Acceptance Criteria
- [ ] Explicit skills-only/runner suspension selects the inline lane and persists across continuation/compaction until the user lifts it.
- [ ] Canonical ticket/CandidateRef input and standalone verification require no runner issuer or synthetic ledger.
- [ ] Autopilot's default lane remains supported when allowed; missing its skill does not block inline readiness.
- [ ] Delivery and exact-head local synchronization are separately authorized caller operations, with current evidence/readback, settings preservation, version/digest checks, and truthful reload reporting.
- [ ] Prior evidence, failures, gates, retry consumption, and non-independent review limitations remain explicit; no test or provider result is invented.
- [ ] The connected references and policy have focused regression coverage, with executed versus unexecuted verification stated accurately.

## Frontier
Implementation authorized by the user's harness-repair-first request. Verification execution,
provider delivery, and local installation retain their separate existing scope and gates.
No Autopilot invocation is permitted for this slice.

## Step-by-Step Implementation Plan
1. Correct the injected policy and readiness/status wording.
2. Align router, ticket producer, execution and verification ownership around the existing contracts.
3. Document the single skills-only reference and add focused regression cases.
4. Inspect the final candidate and record actual evidence/gaps before separately authorized delivery.

## Testing Plan
Static policy/contract review, syntax and local-link checks; focused extension regressions
when execution is allowed. No automatic reruns or full-suite invocation. Live Pi adoption
requires a later user-controlled reload and is not claimed by source checks.

## Out of Scope
- Runner execution, ledger reconciliation, PCG-01, wiki synchronization, or worktree cleanup.
- Authorization renewal, global Pi timeouts, benchmarks, or unrelated settings/packages.
