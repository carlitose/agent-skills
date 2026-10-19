---
type: source
title: "JRS-01 — Jev request shadow extension"
identity_key: ticket:jev-request-shadow/JRS-01
identity_strength: stable
source_path: docs/tickets/jev-request-shadow/done/01-shadow-extension.md
source_digest: sha256:b1a1d773e3a4c26a9e1435fcfdedae4dcf7fa3046acc65edba64d540f026330e
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-10-15
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# JRS-01 — Jev request shadow extension

Compiled from `docs/tickets/jev-request-shadow/done/01-shadow-extension.md`. Identity is `ticket:jev-request-shadow/JRS-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-15** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-jev-request-shadow-spec]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[],"status":"not-identified"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/ticket-jev-request-shadow-jrs-01.md","payload_bytes":2141,"payload_sha256":"b1a1d773e3a4c26a9e1435fcfdedae4dcf7fa3046acc65edba64d540f026330e"}],"payload_bytes":2141,"payload_sha256":"b1a1d773e3a4c26a9e1435fcfdedae4dcf7fa3046acc65edba64d540f026330e","schema":1,"source_digest":"sha256:b1a1d773e3a4c26a9e1435fcfdedae4dcf7fa3046acc65edba64d540f026330e","source_identity":"ticket:jev-request-shadow/JRS-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | no matching section identified in the source; complete source retained |
| frontier | 5: Frontier |
| exclusions | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2141,"payload_sha256":"b1a1d773e3a4c26a9e1435fcfdedae4dcf7fa3046acc65edba64d540f026330e","schema":1,"source_digest":"sha256:b1a1d773e3a4c26a9e1435fcfdedae4dcf7fa3046acc65edba64d540f026330e","source_identity":"ticket:jev-request-shadow/JRS-01"} -->
```markdown
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

```
