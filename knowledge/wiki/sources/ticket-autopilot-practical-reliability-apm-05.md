---
type: source
title: "Bound Git/provider commands with timeout, cancellation, and output limits"
identity_key: ticket:autopilot-practical-reliability/APM-05
identity_strength: stable
source_path: docs/tickets/autopilot-practical-reliability/done/05-bounded-commands.md
source_digest: sha256:a682fce5b27d622c29b0c2dc07fc254c2724f77285b9c6c4177eb5488324679c
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-07
created_provenance: git-commit
disposition_changed: 2026-09-09
disposition_changed_provenance: git-rename
run_id: apm-local-recovery-23257eb8
---

# Bound Git/provider commands with timeout, cancellation, and output limits

Compiled from `docs/tickets/autopilot-practical-reliability/done/05-bounded-commands.md`. Identity is `ticket:autopilot-practical-reliability/APM-05`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-07** via `git-commit`
- Disposition changed: **2026-09-09** via `git-rename`

## Graph

- Parent source: [[sources/artifact-autopilot-practical-reliability]]
- Blocked by: [[sources/ticket-autopilot-practical-reliability-apm-09]] — `ticket:autopilot-practical-reliability/APM-09`

## Run

Completed under autopilot run `apm-local-recovery-23257eb8`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-practical-reliability-apm-05.md","payload_bytes":3688,"payload_sha256":"a682fce5b27d622c29b0c2dc07fc254c2724f77285b9c6c4177eb5488324679c"}],"payload_bytes":3688,"payload_sha256":"a682fce5b27d622c29b0c2dc07fc254c2724f77285b9c6c4177eb5488324679c","schema":1,"source_digest":"sha256:a682fce5b27d622c29b0c2dc07fc254c2724f77285b9c6c4177eb5488324679c","source_identity":"ticket:autopilot-practical-reliability/APM-05","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3688,"payload_sha256":"a682fce5b27d622c29b0c2dc07fc254c2724f77285b9c6c4177eb5488324679c","schema":1,"source_digest":"sha256:a682fce5b27d622c29b0c2dc07fc254c2724f77285b9c6c4177eb5488324679c","source_identity":"ticket:autopilot-practical-reliability/APM-05"} -->
```markdown
---
ticket_schema: 1
ticket_id: "APM-05"
execution_mode: AFK
blocked_by:
  - "APM-09"
---

# Bound Git/provider commands with timeout, cancellation, and output limits

## Artifact Graph
- Artifact ID: `artifact:autopilot-practical-reliability-apm-05`
- Role: `ticket`
- Parent: [Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md)

## Parent Spec
[Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md) — S5 — Bounded Command Execution.

## What to Build
Bound the common command execution path in git_ops.py and its provider consumers so a hanging or noisy subprocess cannot indefinitely stall AFK progress or grow captured output without limit. Integrate explicit failures with existing reporting/readback rather than creating another orchestration or audit system. Reuse the provider-specific strict decoding boundary established by APM-09 (parent spec S9); bounded capture must not reintroduce one global stdout codec.

## Acceptance Criteria
- [ ] Common Git/provider calls have documented finite configurable timeout and output limits, validated before launch and used by the default executor.
- [ ] Hanging and canceled local commands terminate and their child processes are reaped on supported platforms; waiting is bounded and the caller receives a specific failure reason.
- [ ] Output-limit failures never present partial JSON, SHAs, or payloads as complete data; data decoding remains strict and diagnostic decoding retains its current behavior.
- [ ] A timed-out mutating provider call is reported as uncertain, not failed-with-no-effect or successful. Existing readback is used before another mutation attempt; no blind retry is added.
- [ ] Tests prove the default executor path, diagnostic propagation, and lack of surviving test children using disposable local processes. No credentialed provider experiment is required.
- [ ] Configuration/defaults are documented and small; no second ledger, retry framework, or extra authorization protocol is introduced.

## Frontier
Dependency-blocked on APM-09 so command bounding preserves the established provider encoding boundary. No unresolved product decision; missing execution environments must be reported.

Execute inline. AFK does not authorize subagents; explicit user request is required. This ticket does not authorize provider publication or merge.

## Step-by-Step Implementation Plan
1. Trace CommandRunner, SubprocessCommandRunner, provider callers, and current error/readback handling; identify the commands that can mutate external state.
2. Implement bounded capture, configurable finite deadlines, and child-process cancellation at the existing execution seam, preserving the data/diagnostic distinction.
3. Map timeout/cancellation/output-limit results to existing caller diagnostics and uncertain-mutation readback; keep retry decisions outside the raw subprocess wrapper.
4. Run local hanging/noisy/child-process tests and focused Git/provider/CLI regressions, documenting chosen defaults and unsupported environment boundaries.

## Testing Plan
- Disposable sleeping, noisy, nonzero-exit, invalid-UTF-8, and child-spawning programs; verify wall-time bounds and child cleanup.
- Simulated provider mutation accepted before transport timeout, followed by readback, proving no duplicate mutation attempt. This is not live-provider evidence.

These are planned checks, not evidence that implementation or verification has occurred.

## Out of Scope
- General automatic retries, a new workflow framework, or a ledger/schema redesign.
- Killing unrelated processes, real provider mutations, and weakening literal output semantics.

```
