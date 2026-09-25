---
type: source
title: "SH-01 — Support skills-only inline execution"
identity_key: ticket:skills-only-inline-execution/SH-01
identity_strength: stable
source_path: docs/tickets/skills-only-inline-execution/01-skills-only-inline.md
source_digest: sha256:1d8e45af0ddd4d42251864b2f22015197eb706af2e43fb1d06342841c96b7edf
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-20
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# SH-01 — Support skills-only inline execution

Compiled from `docs/tickets/skills-only-inline-execution/01-skills-only-inline.md`. Identity is `ticket:skills-only-inline-execution/SH-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-20** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-skills-only-inline-execution]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-skills-only-inline-execution-sh-01.md","payload_bytes":2684,"payload_sha256":"1d8e45af0ddd4d42251864b2f22015197eb706af2e43fb1d06342841c96b7edf"}],"payload_bytes":2684,"payload_sha256":"1d8e45af0ddd4d42251864b2f22015197eb706af2e43fb1d06342841c96b7edf","schema":1,"source_digest":"sha256:1d8e45af0ddd4d42251864b2f22015197eb706af2e43fb1d06342841c96b7edf","source_identity":"ticket:skills-only-inline-execution/SH-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2684,"payload_sha256":"1d8e45af0ddd4d42251864b2f22015197eb706af2e43fb1d06342841c96b7edf","schema":1,"source_digest":"sha256:1d8e45af0ddd4d42251864b2f22015197eb706af2e43fb1d06342841c96b7edf","source_identity":"ticket:skills-only-inline-execution/SH-01"} -->
```markdown
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

```
