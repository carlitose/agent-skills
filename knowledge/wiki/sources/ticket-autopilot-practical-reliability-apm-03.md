---
type: source
title: "Isolate Git fixtures and make line-ending behavior explicit"
identity_key: ticket:autopilot-practical-reliability/APM-03
identity_strength: stable
source_path: docs/tickets/autopilot-practical-reliability/done/03-hermetic-git-tests.md
source_digest: sha256:a2fe38d8021a194cd61a2da110ba180caf0791a338f341052ac64b822b79d669
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-07
created_provenance: git-commit
disposition_changed: 2026-09-07
disposition_changed_provenance: git-rename
run_id: apm-practical-reliability
---

# Isolate Git fixtures and make line-ending behavior explicit

Compiled from `docs/tickets/autopilot-practical-reliability/done/03-hermetic-git-tests.md`. Identity is `ticket:autopilot-practical-reliability/APM-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-07** via `git-commit`
- Disposition changed: **2026-09-07** via `git-rename`

## Graph

- Parent source: [[sources/artifact-autopilot-practical-reliability]]
- Blocked by: [[sources/ticket-autopilot-practical-reliability-apm-02]] — `ticket:autopilot-practical-reliability/APM-02`

## Run

Completed under autopilot run `apm-practical-reliability`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-practical-reliability-apm-03.md","payload_bytes":3138,"payload_sha256":"a2fe38d8021a194cd61a2da110ba180caf0791a338f341052ac64b822b79d669"}],"payload_bytes":3138,"payload_sha256":"a2fe38d8021a194cd61a2da110ba180caf0791a338f341052ac64b822b79d669","schema":1,"source_digest":"sha256:a2fe38d8021a194cd61a2da110ba180caf0791a338f341052ac64b822b79d669","source_identity":"ticket:autopilot-practical-reliability/APM-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3138,"payload_sha256":"a2fe38d8021a194cd61a2da110ba180caf0791a338f341052ac64b822b79d669","schema":1,"source_digest":"sha256:a2fe38d8021a194cd61a2da110ba180caf0791a338f341052ac64b822b79d669","source_identity":"ticket:autopilot-practical-reliability/APM-03"} -->
```markdown
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

```
