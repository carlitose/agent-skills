---
ticket_schema: 1
ticket_id: "APM-08"
execution_mode: AFK
blocked_by:
  - "APM-04"
  - "APM-05"
---

# Report local phase durations and retries from existing observations

## Artifact Graph
- Artifact ID: `artifact:autopilot-practical-reliability-apm-08`
- Role: `ticket`
- Parent: [Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md)

## Parent Spec
[Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md) — S8 — Local Operational Measurements.

## What to Build
Provide a small local operational report over existing run/leaf/command observations so subsequent efficiency work targets measured slow phases and retries. Reuse current status/budget fields; this is not a new telemetry service or the separate live-token research ticket.

## Acceptance Criteria
- [ ] A local report shows recorded per-phase durations, retry counts, slowest observed phases, and unavailable measurements with explicit source and units.
- [ ] Missing observations remain unavailable rather than zero; leaf-reported time is not labeled total session time and static bytes are not labeled model tokens.
- [ ] Equivalent controlled runs can be compared using documented inputs and environment metadata; no general speedup claim is made from incomparable samples.
- [ ] Reading/reporting existing observations does not mutate the run ledger, consume a leaf interaction, contact a provider, or create a release gate.
- [ ] No prompts, transcripts, credentials, or external telemetry are collected. Existing live-token ownership is referenced rather than duplicated.

## Frontier
Dependency-blocked by APM-04, APM-05.

Execute inline. AFK does not authorize subagents; explicit user request is required. This ticket does not authorize provider publication or merge.

## Step-by-Step Implementation Plan
1. Inspect existing Kernel.report/status fields, resource accounting, and bounded-command outcomes; identify exactly which measurements are already observable.
2. Implement a small read-only local report using those observations and explicit unavailable values; avoid schema expansion unless a genuinely required value cannot be represented, in which case report the gap instead of broadening this ticket.
3. Add deterministic complete/partial-observation examples and a controlled comparison that identifies phase costs without executing provider operations.
4. Document source/units/limitations and run the reporting plus existing status/ledger-purity tests.

## Testing Plan
- Recorded complete and incomplete phase observations, zero recorded duration versus unavailable, retries, and deterministic ordering.
- Before/after ledger byte equality and no-provider-call assertions for report generation; controlled local comparison with no model-cost inference.

These are planned checks, not evidence that implementation or verification has occurred.

## Out of Scope
- Daemon, external telemetry, new database, session/transcript ingestion, or generalized benchmarking infrastructure.
- New release gates, historical-state mutation, or replacing the existing live-token investigation.
