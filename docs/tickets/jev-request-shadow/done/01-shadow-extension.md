---
ticket_schema: 1
ticket_id: "JRS-01"
execution_mode: AFK
blocked_by: []
---

# JRS-01 — Jev request shadow extension

## Artifact Graph
- Artifact ID: `ticket:jev-request-shadow:01`
- Role: `ticket`
- Parent: [jev-request-shadow.md](../../../specs/jev-request-shadow.md)

## Parent Spec
[jev-request-shadow.md](../../../specs/jev-request-shadow.md)

## What to Build
`extensions/jev-request-shadow.ts`: off by default; when on, it asks Jev whether each new user
request is precise or vague and logs the answer without changing anything. `/jev-shadow
on|off|status|report`.

## Acceptance Criteria
- [x] Off by default; `on`/`off` persist in `<agent-dir>/agent-skills/jev-request-shadow.json`.
- [x] When on, one request per eligible user input (after stripping `/skill:ask-skills `), with
  the last assistant text tail as context; commands, `!`, blanks and extension input send nothing.
- [x] The input handler returns at once; failures and timeouts are logged and never thrown.
- [x] The JSONL log has lengths, Noul, verdict, tokens, latency or error, and no message text.
- [x] `status` reports state and key presence; `report` summarizes the log.
- [x] Listed in `package.json` `pi.extensions`; tests pass.

## Frontier
Ready.

## Gates
- Attempt: the work up to merge, local sync and `/jev-shadow on`.
- Budget, time and maximum attempts: not set.
- Approvals: see the spec.
- Exact version: none.
- Existing blocks: none.

## Blocked by
None — can start immediately.

## Evidence
- PR [#480](https://github.com/carlitose/agent-skills/pull/480), implementation commit `5277c30c1e24b009ec96702e67bce09c2f53e4c9`; CI 8/8 green (Prepare profile, 6 shards, local-profile).
- `node --test extensions/*.test.ts` 48/48, with 7 new cases in `extensions/jev-request-shadow.test.ts` (eligibility, off by default, request shape and text-free log, persisted on/off, vague/HTTP/timeout/invalid logged without throwing, no key, report).
- Pi's `emitInput` chains handlers, so the shadow sees the `/skill:ask-skills ` prefix from `mandatory-agent-skills` and strips it.
- Live check after local sync: see the PR thread and the session report.
