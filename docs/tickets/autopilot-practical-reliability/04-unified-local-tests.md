---
ticket_schema: 1
ticket_id: "APM-04"
execution_mode: AFK
blocked_by:
  - "APM-03"
---

# Provide one cross-platform quick/full local test entry point

## Artifact Graph
- Artifact ID: `artifact:autopilot-practical-reliability-apm-04`
- Role: `ticket`
- Parent: [Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md)

## Parent Spec
[Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md) — S4 — Unified Local Tests.

## What to Build
Make the ordinary local test workflow include the TypeScript extension tests and Python checks instead of leaving npm test as an extension-only signal. Provide documented quick/full selection with explicit scope, prerequisites, exit behavior, and skips using the current test frameworks.

## Acceptance Criteria
- [ ] A documented entry point offers quick and full modes and runs the appropriate extension and Python suites on supported Windows/POSIX environments.
- [ ] Quick mode names included and omitted scopes; full mode includes all intended suites. Neither mode implies live-provider verification.
- [ ] Any failing suite, unavailable required interpreter, or invalid selector produces a nonzero result and an actionable message; Python is never silently omitted.
- [ ] Reported counts distinguish succeeded, failed, errored, skipped, and not-run checks; native platform evidence is not inferred from simulated branches.
- [ ] Usage and prerequisites match the actual package configuration. No hosted CI, provider policy, global installation, or extra test framework is introduced.

## Frontier
Dependency-blocked by APM-03.

Execute inline. AFK does not authorize subagents; explicit user request is required. This ticket does not authorize provider publication or merge.

## Step-by-Step Implementation Plan
1. Inspect package.json, the existing Python discovery conventions, forward-test selectors, and prerequisite documentation.
2. Implement a small cross-platform orchestrator or minimal package commands that reuse the existing runners and propagate their results.
3. Test selection and exit propagation with controlled runner outcomes, then execute real quick/full scopes as available.
4. Document exact commands, omitted scopes, and environment requirements without making the quick command a whole-suite claim.

## Testing Plan
- Controlled success/failure/missing-tool/invalid-selector cases for both runner families.
- Real quick and full runs with aggregate and per-suite outcomes; explicitly report any unavailable platform or prerequisite.

These are planned checks, not evidence that implementation or verification has occurred.

## Out of Scope
- Activating GitHub Actions or another hosted CI service.
- Changing release/merge gates or hiding existing test failures behind exclusions.
