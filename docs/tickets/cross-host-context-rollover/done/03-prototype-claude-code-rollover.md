---
ticket_schema: 1
ticket_id: "CR-03"
execution_mode: AFK
blocked_by:
  - "CR-01"
---

# Prototype Claude Code rollover

## Artifact Graph

- Artifact ID: `artifact:cr-03-prototype-claude-code-rollover`
- Role: `ticket`
- Parent: [Cross-host Context Rollover](../../specs/cross-host-context-rollover-wayfinder.md)

## Parent Spec

[Cross-host Context Rollover](../../specs/cross-host-context-rollover-wayfinder.md)

## Type

Prototype

## What to Prototype

Build the Claude Code tracer bullet for the policy frozen by `CR-01`. Use a disposable
controller around `--input-format stream-json`, `--output-format stream-json`,
`--include-hook-events`, and UUID-bound sessions to observe the decided message projection
prospectively, checkpoint a validated handoff, start a fresh session, and submit the
bootstrap prompt.

Compare the controller path with `SessionStart`, `Stop`, `PreCompact`, and `PostCompact`
hooks. Treat transcript access as diagnostic or explicitly version-bound evidence, not as
the portable count contract. Record whether the installed interactive clear path can be
driven safely; do not infer it from hook names or changelog entries.

Drive the trigger from current status-line context data:
`context_window.total_input_tokens + context_window.total_output_tokens`. Arm
`rollover_pending` at 150,000, then wait for `Stop` plus the policy's semantic task boundary.
Set or verify `--autocompact <tokens>` above 150,000. Treat it and `PreCompact` only as
version-bound preservation boundaries for an already pending generation; neither may arm
early or prove creation of a fresh UUID-bound session.

## Acceptance Criteria

- [ ] A stream fixture projects the exact `CR-01` message semantics and emits the same
      versioned user, assistant, and total count shape as the Codex prototype.
- [ ] Partial chunks, hook lifecycle events, tool calls, forwarded subagent text, and replayed
      user messages cannot double-count a visible message.
- [ ] The context-window percentage and `PreCompact` event are reported separately from the
      message count.
- [ ] Status-line fixtures prove `149999` remains monitoring, `150000` arms pending,
      cumulative cost/session totals cannot arm, null pre-first-call usage waits, and
      `context_window_size <= 150000` fails configuration.
- [ ] Rollover waits for a completed stop boundary and validates the private handoff before
      starting a new UUID-bound session.
- [ ] The fresh session receives only the handoff path and reconstruction instructions, then
      reads the Wayfinder map, ticket inventory, runner status, and next frontier.
- [ ] Missing, expired, mismatched, consumed, or malformed state fails closed and leaves the
      previous session resumable.
- [ ] The prototype records which behavior came from stream control, which came from hooks,
      and which still requires the live `CR-04` boundary.
- [ ] No global hook installation, credentials, transcript copying, or production claim is
      introduced.

## Frontier

Blocked by `CR-01`. The prototype must preserve the fixed threshold, safe boundary, and
controller authority; it cannot choose its own message semantics, registry, or compaction
fallback.

## Step-by-Step Implementation Plan

1. Capture sanitized synthetic stream and hook fixtures for the installed Claude Code
   command surface.
2. Project current status-line input/output totals into the 150,000-token pending state and
   project complete messages without counting partial chunks or replay events twice.
3. Implement the guarded safe-boundary, temp-handoff, and registry transition against
   fixtures.
4. Start a synthetic new UUID-bound session with the bootstrap prompt.
5. Reconstruct Wayfinder and ticket-autopilot state from fixture pointers.
6. Probe the hook-only and interactive-clear boundaries and record unknowns explicitly.

## Testing Plan

Fixtures for complete and partial messages, replayed user messages, forwarded subagent text,
hook events, context-pressure events, threshold edges, handoff validation, registry
collisions, and one-shot restore. Keep authenticated and interactive UI proof in `CR-04`.

## Out of Scope

- Shipping a production Claude Code plugin, global settings change, or background daemon.
- Treating the raw transcript layout as a provider-neutral interface.
- Reusing or forking the old session when the confirmed policy requires a truly fresh one.
- Claiming message count represents token usage or remaining context.
