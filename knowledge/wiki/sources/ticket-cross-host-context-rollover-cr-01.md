---
type: source
title: "Freeze the rollover policy"
identity_key: ticket:cross-host-context-rollover/CR-01
identity_strength: stable
source_path: docs/tickets/cross-host-context-rollover/done/01-freeze-rollover-policy.md
source_digest: sha256:dc22da6f30dd6b36d9a3c05d3eb50d76988c5cf55dcc3bb4e1eea8f3ab6b7267
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-11
created_provenance: git-commit
disposition_changed: 2026-08-11
disposition_changed_provenance: git-rename
run_id: 1e9bd66dc83e435d
---

# Freeze the rollover policy

Compiled from `docs/tickets/cross-host-context-rollover/done/01-freeze-rollover-policy.md`. Identity is `ticket:cross-host-context-rollover/CR-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-11** via `git-commit`
- Disposition changed: **2026-08-11** via `git-rename`

## Graph

- Parent source: [[sources/artifact-cross-host-context-rollover-wayfinder]]

## Run

Completed under autopilot run `1e9bd66dc83e435d`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[6],"status":"present"},"exclusions":{"headings":[10],"status":"present"},"frontier":{"headings":[7],"status":"present"},"intent":{"headings":[],"status":"not-identified"},"testing":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-cross-host-context-rollover-cr-01.md","payload_bytes":5149,"payload_sha256":"dc22da6f30dd6b36d9a3c05d3eb50d76988c5cf55dcc3bb4e1eea8f3ab6b7267"}],"payload_bytes":5149,"payload_sha256":"dc22da6f30dd6b36d9a3c05d3eb50d76988c5cf55dcc3bb4e1eea8f3ab6b7267","schema":1,"source_digest":"sha256:dc22da6f30dd6b36d9a3c05d3eb50d76988c5cf55dcc3bb4e1eea8f3ab6b7267","source_identity":"ticket:cross-host-context-rollover/CR-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | no matching section identified in the source; complete source retained |
| acceptance | 6: Acceptance Criteria |
| testing | 9: Testing Plan |
| frontier | 7: Frontier |
| exclusions | 10: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":5149,"payload_sha256":"dc22da6f30dd6b36d9a3c05d3eb50d76988c5cf55dcc3bb4e1eea8f3ab6b7267","schema":1,"source_digest":"sha256:dc22da6f30dd6b36d9a3c05d3eb50d76988c5cf55dcc3bb4e1eea8f3ab6b7267","source_identity":"ticket:cross-host-context-rollover/CR-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "CR-01"
execution_mode: HITL
blocked_by: []
---

# Freeze the rollover policy

## Artifact Graph

- Artifact ID: `artifact:cr-01-freeze-rollover-policy`
- Role: `ticket`
- Parent: [Cross-host Context Rollover](../../specs/cross-host-context-rollover-wayfinder.md)

## Parent Spec

[Cross-host Context Rollover](../../specs/cross-host-context-rollover-wayfinder.md)

## Type

Grilling

## Confirmed Inputs

- Arm at `current_context_tokens >= 150000`; `149999` does not arm and `150000` does.
- Crossing the threshold sets a source-session-bound `rollover_pending` flag and never
  interrupts an active task.
- Execute rollover after the current task stops, or before accepting the next task when the
  flag is pending and no task is active.
- A safe task boundary requires no active host turn. If an explicit Codex goal or
  ticket-autopilot ticket owns multi-turn work, that owner must also be terminal. Otherwise
  `Stop`/`turn/completed` is the boundary. Hold a pending next prompt until restore.
- Use current live-context usage, not cumulative session usage. Codex projects
  `tokenUsage.last.totalTokens`; Claude Code projects
  `context_window.total_input_tokens + context_window.total_output_tokens`.
- The target mode is controller-managed automation. The generic `handoff` skill stays
  explicit-only; a narrow controller entry point must preserve its privacy, redaction,
  expiry, and pointer-only contract.

## What to Decide

Freeze the provider-neutral policy before either host adapter is prototyped. Run the
canonical `grilling` interview one question at a time and record the confirmed result
through `to-spec`.

The decision must cover:

- what one chat message means, including whether commentary, final answers, tool calls,
  reasoning, plans, and compaction markers count;
- whether user and assistant counts are reported separately as well as in total;
- trigger hysteresis and loop prevention after restore without changing the confirmed
  150,000-token arming edge;
- whether compaction plus bootstrap is an acceptable fallback when a true new session is
  unavailable;
- how the latest handoff is bound to the workspace and source session without selecting an
  arbitrary temp file by timestamp;
- whether the generic `handoff` skill stays explicit-only and a narrower rollover entry
  point owns automation.

## Acceptance Criteria

- [ ] A decision spec records the message projection with examples for both Codex tagged
      items and Claude Code stream events.
- [ ] User, assistant, tool, reasoning, commentary, and compaction cases are each included
      or excluded explicitly.
- [ ] The trigger distinguishes message count from context usage and states the exact
      `149999`/`150000` edge, pending transition, safe boundary, and hard-fallback behavior.
- [ ] Codex uses `tokenUsage.last.totalTokens` and rejects accumulated `tokenUsage.total`;
      Claude Code uses current status-line input/output totals rather than cumulative cost.
- [ ] Rollover is impossible while a host turn is active, remains pending while an explicit
      goal/ticket owner is non-terminal, and holds rather than loses a submitted next task.
- [ ] `PreCompact` preserves an already pending generation, but cannot arm before 150,000;
      an earlier effective auto-compaction boundary fails configuration visibly.
- [ ] The authority model says who may create the handoff, end or replace the chat, and
      submit the bootstrap turn, preserving the confirmed controller-managed direction.
- [ ] The decision preserves or deliberately replaces `disable-model-invocation: true` and
      `allow_implicit_invocation: false`, with the security rationale recorded.
- [ ] Registry binding, expiry, consumption, retries, and multi-chat collision behavior are
      deterministic.
- [ ] Rejected options include raw transcript parsing as the portable contract and
      timestamp-only latest-handoff discovery.
- [ ] The parent map links the decision and `artifact-audit` reports no new errors.

## Frontier

Ready. This decision blocks both host tracer bullets because changing the message
projection, trigger, or automation authority changes their observable contract.

## Step-by-Step Implementation Plan

1. Record the confirmed 150,000-token arming edge and current-context projections verbatim.
2. Ask the message-projection question for informational reporting.
3. Freeze fallback, loop-prevention, and handoff-registry behavior without reopening the
   controller-managed direction.
4. Record the resulting decision through `to-spec`, including rejected alternatives.
5. Link the decision from the parent map and replace the resolved unknowns.

## Testing Plan

No runtime behavior changes. Validate the decision artifact, reciprocal graph links, and
examples against the current Codex App Server item types and Claude Code stream/hook facts.

## Out of Scope

- Implementing a hook, controller, transcript parser, or session launcher.
- Changing the confirmed 150,000-token threshold during implementation without a new policy
  decision.
- Running a live clear or creating a real provider session.

```
