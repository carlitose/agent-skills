---
type: source
title: "ASD-01 — Defer the active Pi session"
identity_key: ticket:llm-wiki-active-session-deferral/ASD-01
identity_strength: stable
source_path: docs/tickets/llm-wiki-active-session-deferral/done/ASD-01-defer-active-pi-session.md
source_digest: sha256:c73249e34938250ce0ecf4453968af8e5f3ef119a762e36e59dbca6a94d1aea7
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-19
created_provenance: git-commit
disposition_changed: 2026-09-19
disposition_changed_provenance: git-rename
run_id: active-session-deferral-v2
---

# ASD-01 — Defer the active Pi session

Compiled from `docs/tickets/llm-wiki-active-session-deferral/done/ASD-01-defer-active-pi-session.md`. Identity is `ticket:llm-wiki-active-session-deferral/ASD-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-19** via `git-commit`
- Disposition changed: **2026-09-19** via `git-rename`

## Graph

- Parent source: [[sources/spec-llm-wiki-active-session-deferral]]

## Run

Completed under autopilot run `active-session-deferral-v2`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[7],"status":"present"},"frontier":{"headings":[],"status":"not-identified"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[6],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-active-session-deferral-asd-01.md","payload_bytes":2466,"payload_sha256":"c73249e34938250ce0ecf4453968af8e5f3ef119a762e36e59dbca6a94d1aea7"}],"payload_bytes":2466,"payload_sha256":"c73249e34938250ce0ecf4453968af8e5f3ef119a762e36e59dbca6a94d1aea7","schema":1,"source_digest":"sha256:c73249e34938250ce0ecf4453968af8e5f3ef119a762e36e59dbca6a94d1aea7","source_identity":"ticket:llm-wiki-active-session-deferral/ASD-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 6: Testing Plan |
| frontier | no matching section identified in the source; complete source retained |
| exclusions | 7: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2466,"payload_sha256":"c73249e34938250ce0ecf4453968af8e5f3ef119a762e36e59dbca6a94d1aea7","schema":1,"source_digest":"sha256:c73249e34938250ce0ecf4453968af8e5f3ef119a762e36e59dbca6a94d1aea7","source_identity":"ticket:llm-wiki-active-session-deferral/ASD-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "ASD-01"
execution_mode: AFK
blocked_by: []
---

# ASD-01 — Defer the active Pi session

## Artifact Graph
- Artifact ID: `ticket:llm-wiki-active-session-deferral:ASD-01`
- Role: `ticket`
- Parent: [Defer the active Pi session during wiki sync](../../specs/llm-wiki-active-session-deferral.md)

## Parent Spec
[Defer the active Pi session during wiki sync](../../specs/llm-wiki-active-session-deferral.md)

## What to Build
Teach `session_ingest` to recognize the exact active Pi transcript exposed by
`PI_SESSION_FILE`, defer it before extraction, and report the deferral explicitly. Add `pi` to the
tracked agent-skills binding in the same bounded candidate so the already-implemented provider is
actually adopted. Preserve every other provider, incremental-memory, redaction, pointer, digest,
catalog, and lint behavior.

## Acceptance Criteria
- [ ] AC1: A discovered Pi transcript equal to `PI_SESSION_FILE` is not opened or extracted and
  produces one structured `active-session` entry in `deferred`.
- [ ] AC2: The deferred transcript is not counted as written, skipped, or refused; provider and
  session totals remain truthful.
- [ ] AC3: Missing, malformed, or unrelated `PI_SESSION_FILE` values do not defer another file;
  non-Pi providers are never deferred by this variable.
- [ ] AC4: Prior Pi sessions are still ingested and a formerly active transcript is ingested once
  the environment points at a different session.
- [ ] AC5: The tracked agent-skills binding explicitly includes `pi`, while unrelated bindings
  and provider discovery remain unchanged.
- [ ] AC6: Focused session-ingest and sync tests plus the required Linux profile pass; no Windows
  full gate is required.

## Implementation Plan
1. Add causal report and fail-on-read tests.
2. Add one narrow active-Pi identity predicate and defer before incremental/full extraction.
3. Add Pi explicitly to the tracked project binding and prove the live project defers only the
   current session while ingesting closed sessions.
4. Run focused and required QA, review the frozen diff, and deliver through a normal PR.

## Testing Plan
Use temporary transcripts and patched discovery. Assert extraction is never called for the active
file, then cover unrelated/missing environment values and a closed Pi session.

## Out of Scope
Partial parsing, append checkpoints, provider discovery changes, wiki-PR merge authority, or
cleanup of unrelated worktrees.

```
