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
- Parent: [jev-request-shadow.md](../../specs/jev-request-shadow.md)

## Parent Spec
[jev-request-shadow.md](../../specs/jev-request-shadow.md)

## What to Build
`extensions/jev-request-shadow.ts`: off by default; when on, it asks Jev whether each new user
request is precise or vague and logs the answer without changing anything. `/jev-shadow
on|off|status|report`.

## Acceptance Criteria
- [ ] Off by default; `on`/`off` persist in `<agent-dir>/agent-skills/jev-request-shadow.json`.
- [ ] When on, one request per eligible user input (after stripping `/skill:ask-skills `), with
  the last assistant text tail as context; commands, `!`, blanks and extension input send nothing.
- [ ] The input handler returns at once; failures and timeouts are logged and never thrown.
- [ ] The JSONL log has lengths, Noul, verdict, tokens, latency or error, and no message text.
- [ ] `status` reports state and key presence; `report` summarizes the log.
- [ ] Listed in `package.json` `pi.extensions`; tests pass.

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
