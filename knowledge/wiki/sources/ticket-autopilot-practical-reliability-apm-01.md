---
type: source
title: "Adopt practical prompt defaults and explicit-user-only delegation"
identity_key: ticket:autopilot-practical-reliability/APM-01
identity_strength: stable
source_path: docs/tickets/autopilot-practical-reliability/done/01-practical-prompts.md
source_digest: sha256:bcc7930900a9cb372f51ca298b6d3fb95b058a53b4e99712f7710d60ee2bd260
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-07
created_provenance: git-commit
disposition_changed: 2026-09-07
disposition_changed_provenance: git-rename
run_id: apm-practical-reliability
---

# Adopt practical prompt defaults and explicit-user-only delegation

Compiled from `docs/tickets/autopilot-practical-reliability/done/01-practical-prompts.md`. Identity is `ticket:autopilot-practical-reliability/APM-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-07** via `git-commit`
- Disposition changed: **2026-09-07** via `git-rename`

## Graph

- Parent source: [[sources/artifact-autopilot-practical-reliability]]

## Run

Completed under autopilot run `apm-practical-reliability`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-practical-reliability-apm-01.md","payload_bytes":3617,"payload_sha256":"bcc7930900a9cb372f51ca298b6d3fb95b058a53b4e99712f7710d60ee2bd260"}],"payload_bytes":3617,"payload_sha256":"bcc7930900a9cb372f51ca298b6d3fb95b058a53b4e99712f7710d60ee2bd260","schema":1,"source_digest":"sha256:bcc7930900a9cb372f51ca298b6d3fb95b058a53b4e99712f7710d60ee2bd260","source_identity":"ticket:autopilot-practical-reliability/APM-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3617,"payload_sha256":"bcc7930900a9cb372f51ca298b6d3fb95b058a53b4e99712f7710d60ee2bd260","schema":1,"source_digest":"sha256:bcc7930900a9cb372f51ca298b6d3fb95b058a53b4e99712f7710d60ee2bd260","source_identity":"ticket:autopilot-practical-reliability/APM-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "APM-01"
execution_mode: AFK
blocked_by: []
---

# Adopt practical prompt defaults and explicit-user-only delegation

## Artifact Graph
- Artifact ID: `artifact:autopilot-practical-reliability-apm-01`
- Role: `ticket`
- Parent: [Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md)

## Parent Spec
[Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md) — S1 — Practical Prompt Defaults.

## What to Build
Implement the parent's two-row prompt-defaults table in repository-owned operating guidance and applicable prompt entry points. Preserve the user's intent: 'Non siamo la CIA o la NSA'; security stays simple and proportionate, and subagents require an explicit user request. Serial inline skill composition is not delegation. Reconcile skill prose that currently suggests delegating just because a worker is available or the task is broad.

## Acceptance Criteria
- [ ] The repository-owned prompts expose both defaults from S1: no advanced security protocols, additional approval layers, or extra procedures without explicit request; no subagents without an explicit user request.
- [ ] Routine tasks, AFK requests, broad research, available worker tools, generic host permission, and silence do not start a subagent. An explicit request permits only the requested delegation scope.
- [ ] The guidance distinguishes inline skill composition from subagents and never labels same-context review independent.
- [ ] Essential secret protection, data integrity, destructive/external-action authorization, and higher-priority mandatory instructions remain intact. No existing runtime protection is removed as a side effect.
- [ ] There is one owning definition and concise pointers from applicable prompt entry points; contradictory default-delegation suggestions are reconciled and covered by repository tests.
- [ ] No installed skill copy, personal/global prompt, or local Pi configuration is changed.

## Frontier
Ready. No unresolved product decision; missing execution environments must be reported.

Execute inline. AFK does not authorize subagents; explicit user request is required. This ticket does not authorize provider publication or merge.

## Step-by-Step Implementation Plan
1. Trace the repository-owned prompt construction in extensions/mandatory-agent-skills.ts and the relevant routing, research, architecture, and orchestration skill instructions; identify actual consumers before editing.
2. Use writing-for-agents to implement the S1 table and concise common-path wording, then replace conflicting default delegation suggestions with pointers or explicit-user-only wording.
3. Add positive and negative prompt/skill contract cases, including an explicit delegation request and ordinary AFK work. Use inline simulations; do not spawn a worker for this ticket.
4. Run the relevant extension and skill graph/invocation/context checks, inspecting any baseline mismatch rather than inflating limits.

## Testing Plan
- Static/integration prompt checks: normal task, large research task, AFK, tool availability, explicit request, and quoted/negated delegation text.
- Existing TypeScript extension tests and relevant Python skill graph/model-invocation/context tests. No external provider or actual subagent is needed.

These are planned checks, not evidence that implementation or verification has occurred.

## Out of Scope
- Changing the delivery lane or merge authorization policy.
- Removing runtime checks, adding a security framework, or applying settings outside this repository.

```
