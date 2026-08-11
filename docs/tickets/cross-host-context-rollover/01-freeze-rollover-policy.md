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
