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
