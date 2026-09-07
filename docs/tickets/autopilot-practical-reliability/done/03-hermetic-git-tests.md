---
ticket_schema: 1
ticket_id: "APM-03"
execution_mode: AFK
blocked_by:
  - "APM-02"
---

# Isolate Git fixtures and make line-ending behavior explicit

## Artifact Graph
- Artifact ID: `artifact:autopilot-practical-reliability-apm-03`
- Role: `ticket`
- Parent: [Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md)

## Parent Spec
[Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md) — S3 — Hermetic Git and Line-Ending Tests.

## What to Build
Remove accidental dependence on the operator's Git configuration and text newline conversion from the final-tree fixtures and related temporary-repository helpers. Preserve exact production byte/digest semantics and make incompatible production source setup fail early with an actionable explanation.

## Acceptance Criteria
- [ ] Temporary-repository tests control relevant Git configuration, hooks/signing defaults, and canonical fixture bytes without modifying user/system Git configuration.
- [ ] The selected eight-module baseline from the parent is rerun with inherited autocrlf=true and process-only autocrlf=false; the shared fixture no longer errors for either accidental EOL normalization or the APM-02 path defect.
- [ ] Intentional LF and CRLF cases are explicit and exercise the real Git clean/index boundary rather than a fake that repeats the implementation assumption.
- [ ] Unsupported production source-byte/index combinations are rejected before projection effects with an actionable diagnostic; input/index bytes and state remain unchanged.
- [ ] No production digest or literal comparison is weakened to make fixtures pass. Any unrelated failure or unavailable/symlink-dependent check is reported separately.

## Frontier
Dependency-blocked by APM-02.

Execute inline. AFK does not authorize subagents; explicit user request is required. This ticket does not authorize provider publication or merge.

## Step-by-Step Implementation Plan
1. Inspect the shared final-tree fixture in test_kernel.py, related temporary-repository helpers, and production source-byte/index preflight.
2. Make fixture configuration and byte writes explicit; isolate relevant Git settings and any command environment inheritance without changing machine-wide settings.
3. Add intentional line-ending variants and early-rejection assertions for unsupported source formats; document the supported setup at the existing operator guidance boundary.
4. Repeat the parent's selected modules in both controlled configurations and run focused source/projection tests.

## Testing Plan
- Real Git fixture tests for LF/CRLF, autocrlf true/false, and deliberately conflicting inherited signing/hooks configuration.
- Byte/index/state comparison before and after rejected projection; complete baseline counts and platform/skip limitations.

These are planned checks, not evidence that implementation or verification has occurred.

## Out of Scope
- Changing global Git configuration or normalizing every repository file.
- Suppressing errors, repairing unrelated red tests, or reopening the historical canceled CI ticket.
