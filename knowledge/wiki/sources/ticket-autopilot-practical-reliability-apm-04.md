---
type: source
title: "Provide one cross-platform quick/full local test entry point"
identity_key: ticket:autopilot-practical-reliability/APM-04
identity_strength: stable
source_path: docs/tickets/autopilot-practical-reliability/done/04-unified-local-tests.md
source_digest: sha256:8354e3b0dbf2d6829dd6b125de28af15a8237b58ddaeff3337e22b127e433a81
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-07
created_provenance: git-commit
disposition_changed: 2026-09-08
disposition_changed_provenance: git-rename
run_id: apm-practical-reliability
---

# Provide one cross-platform quick/full local test entry point

Compiled from `docs/tickets/autopilot-practical-reliability/done/04-unified-local-tests.md`. Identity is `ticket:autopilot-practical-reliability/APM-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-07** via `git-commit`
- Disposition changed: **2026-09-08** via `git-rename`

## Graph

- Parent source: [[sources/artifact-autopilot-practical-reliability]]
- Blocked by: [[sources/ticket-autopilot-practical-reliability-apm-03]] — `ticket:autopilot-practical-reliability/APM-03`

## Run

Completed under autopilot run `apm-practical-reliability`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-practical-reliability-apm-04.md","payload_bytes":2828,"payload_sha256":"8354e3b0dbf2d6829dd6b125de28af15a8237b58ddaeff3337e22b127e433a81"}],"payload_bytes":2828,"payload_sha256":"8354e3b0dbf2d6829dd6b125de28af15a8237b58ddaeff3337e22b127e433a81","schema":1,"source_digest":"sha256:8354e3b0dbf2d6829dd6b125de28af15a8237b58ddaeff3337e22b127e433a81","source_identity":"ticket:autopilot-practical-reliability/APM-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2828,"payload_sha256":"8354e3b0dbf2d6829dd6b125de28af15a8237b58ddaeff3337e22b127e433a81","schema":1,"source_digest":"sha256:8354e3b0dbf2d6829dd6b125de28af15a8237b58ddaeff3337e22b127e433a81","source_identity":"ticket:autopilot-practical-reliability/APM-04"} -->
```markdown
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

```
