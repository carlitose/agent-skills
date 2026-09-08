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
