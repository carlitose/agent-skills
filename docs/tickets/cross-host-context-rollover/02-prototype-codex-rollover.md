---
ticket_schema: 1
ticket_id: "CR-02"
execution_mode: AFK
blocked_by:
  - "CR-01"
---

# Prototype Codex rollover

## Artifact Graph

- Artifact ID: `artifact:cr-02-prototype-codex-rollover`
- Role: `ticket`
- Parent: [Cross-host Context Rollover](../../specs/cross-host-context-rollover-wayfinder.md)

## Parent Spec

[Cross-host Context Rollover](../../specs/cross-host-context-rollover-wayfinder.md)

## Type

Prototype

## What to Prototype

Build a disposable Codex tracer bullet for the policy frozen by `CR-01`. Exercise the
complete count → handoff → new thread → bootstrap → reconstruction path without committing
to a production module boundary.

Use the installed Codex version's generated App Server schema. Count only the decided
`ThreadItem` projection from `thread/read(includeTurns: true)`, preserve the old thread,
create a fresh thread with `thread/start`, and submit the bootstrap through `turn/start`.
Compare that controller path with hook-only `PreCompact`, `PostCompact`, and `SessionStart`
behavior, but do not claim that hooks can issue `/clear` unless observed.

Drive the trigger from `thread/tokenUsage/updated`: use
`tokenUsage.last.totalTokens` as current context, reject cumulative `tokenUsage.total`, arm
`rollover_pending` at 150,000, and wait for `turn/completed` plus the policy's semantic task
boundary. If a new turn is requested while pending, hold it until restore and submit it only
after the bootstrap in the replacement thread.

The bootstrap must receive only the validated handoff path and reconstruction instructions.
It must read the Wayfinder map, run `ticket-list` on the pointed ticket folder, and run
ticket-autopilot `status` when a run ID is present.

## Acceptance Criteria

- [ ] A version-bound App Server fixture counts the exact `CR-01` message projection and
      reports user, assistant, and total counts in versioned JSON.
- [ ] Tool, reasoning, plan, and compaction items follow the confirmed inclusion rules and
      cannot silently change the total.
- [ ] Token fixtures prove `149999` remains monitoring, `150000` arms pending, accumulated
      `tokenUsage.total` cannot arm, and `modelContextWindow <= 150000` fails configuration.
- [ ] Rollover waits for the active turn to stop and refuses to create a fresh thread before
      a private, redacted, unexpired, workspace-bound handoff validates.
- [ ] The old thread remains readable after the new thread starts.
- [ ] The bootstrap reconstructs the map, ticket inventory, run status, and next frontier
      from durable pointers rather than copied ticket or transcript content.
- [ ] A missing, expired, mismatched, consumed, or malformed handoff fails closed without a
      clear/new-thread side effect.
- [ ] The hook-only experiment states exactly what it can automate and what still requires
      the controller or user.
- [ ] No credentials, provider secrets, live token claims, or production installation are
      introduced.

## Frontier

Blocked by `CR-01`. The prototype must preserve the fixed threshold, safe boundary, and
controller authority; it cannot choose its own message semantics, registry, or fallback.

## Step-by-Step Implementation Plan

1. Generate or load the exact installed App Server schema and define disposable fixtures.
2. Project token-usage notifications into the 150,000-token pending state and project
   `thread/read` turns into the informational message-count contract.
3. Implement the guarded safe-boundary, handoff, and one-shot registry transition against
   temp fixtures.
4. Start a synthetic fresh thread and submit a bootstrap turn through a fake or local
   App Server boundary.
5. Reconstruct Wayfinder and ticket-autopilot state from fixture pointers.
6. Probe the hook-only compact/clear boundary and record unsupported behavior explicitly.

## Testing Plan

Unit fixtures for every included and excluded item type, threshold edges, active-turn
rejection, handoff validation failures, registry collisions, and one-shot restore. Add one
local integration harness around the generated App Server schema; leave authenticated and UI
behavior to `CR-04`.

## Out of Scope

- Shipping a production daemon, plugin, or globally installed hook.
- Parsing Codex transcript JSONL as a stable contract.
- Automatically merging or mutating ticket-autopilot run state.
- Claiming desktop deep links submit their prefilled prompt automatically.
