---
type: source
title: "TBP-01 — Let the builder implement a prose task"
identity_key: ticket:ticket-driver-builder-prompt/TBP-01
identity_strength: stable
source_path: docs/tickets/ticket-driver-builder-prompt/done/01-let-the-builder-implement-a-prose-task.md
source_digest: sha256:62be2c7ee86192a3c68712b626e485e0a483a998478c5f9688ff1d4d23881670
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-29
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# TBP-01 — Let the builder implement a prose task

Compiled from `docs/tickets/ticket-driver-builder-prompt/done/01-let-the-builder-implement-a-prose-task.md`. Identity is `ticket:ticket-driver-builder-prompt/TBP-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-29** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-ticket-driver-builder-prompt]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-driver-builder-prompt-tbp-01.md","payload_bytes":2094,"payload_sha256":"62be2c7ee86192a3c68712b626e485e0a483a998478c5f9688ff1d4d23881670"}],"payload_bytes":2094,"payload_sha256":"62be2c7ee86192a3c68712b626e485e0a483a998478c5f9688ff1d4d23881670","schema":1,"source_digest":"sha256:62be2c7ee86192a3c68712b626e485e0a483a998478c5f9688ff1d4d23881670","source_identity":"ticket:ticket-driver-builder-prompt/TBP-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2094,"payload_sha256":"62be2c7ee86192a3c68712b626e485e0a483a998478c5f9688ff1d4d23881670","schema":1,"source_digest":"sha256:62be2c7ee86192a3c68712b626e485e0a483a998478c5f9688ff1d4d23881670","source_identity":"ticket:ticket-driver-builder-prompt/TBP-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TBP-01"
execution_mode: AFK
blocked_by: []
---

# TBP-01 — Let the builder implement a prose task

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-builder-prompt-01`
- Role: `ticket`
- Parent: [ticket-driver-builder-prompt.md](../../specs/ticket-driver-builder-prompt.md)

## Parent Spec
[ticket-driver-builder-prompt.md](../../specs/ticket-driver-builder-prompt.md)

## What to Build
Rewrite `ticket-driver/prompts/builder.md` so the builder treats the supplied task as the whole
assignment. A missing spec or ticket is never a reason to stop, and unfinished work is left as the
best implementation plus prose. Leaf boundaries stay as they are.

## Acceptance Criteria
- [x] The prompt no longer presents a canonical ticket as a precondition, and says a missing one
  is never a reason to stop.
- [x] It keeps the leaf boundaries: no runner, driver or scheduler, no self-certification, the
  worktree only, changes uncommitted.
- [x] Replaying refused requests on copies with the old and the new prompt shows fewer stops for
  protocol with the new one, and the replay spend is recorded.
- [x] All ticket-driver tests pass.

## Outcome
2026-09-29. Four c1a requests of lot `dbh` that had stopped for protocol were rerun on clones of
their cell, once with each prompt, for 0.05 $ in total.
- Old prompt: 2 stops for protocol, 1 give-up, 1 integrated.
- New prompt: 0 stops for protocol, 2 give-ups, 2 integrated.

The ticket-driver tests pass. The prompt hash changes from `c655b1c6...` to `e7cb0af6...`.

## Frontier
Closed. The next driver measurement binds the new prompt hash.

## Step-by-Step Implementation Plan
1. Classify the empty candidates of lot `dbh` from the builder sessions.
2. Rewrite the builder prompt.
3. Replay refused requests on copies with both prompts, then run the driver tests.

## Testing Plan
Behavioral replay on copies (a prompt is not unit-testable for model behavior) and the offline
ticket-driver tests.

## Out of Scope
Give-ups for task size, the output capture limit, fresh-session-per-run, and past lot records.

```
