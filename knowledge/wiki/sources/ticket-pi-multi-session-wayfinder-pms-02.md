---
type: source
title: "PMS-02 — Durable ticket claim across sessions"
identity_key: ticket:pi-multi-session-wayfinder/PMS-02
identity_strength: stable
source_path: docs/tickets/pi-multi-session-wayfinder/02-durable-ticket-claim.md
source_digest: sha256:e6449194cbad54e3b3c68bc2efe44e1ec3830a81b5107a527a3bef224c022c0a
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# PMS-02 — Durable ticket claim across sessions

Compiled from `docs/tickets/pi-multi-session-wayfinder/02-durable-ticket-claim.md`. Identity is `ticket:pi-multi-session-wayfinder/PMS-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-pi-multi-session-wayfinder]]
- Child source: [[sources/artifact-pi-multi-session-claims]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[5],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[4],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-pi-multi-session-wayfinder-pms-02.md","payload_bytes":1926,"payload_sha256":"e6449194cbad54e3b3c68bc2efe44e1ec3830a81b5107a527a3bef224c022c0a"}],"payload_bytes":1926,"payload_sha256":"e6449194cbad54e3b3c68bc2efe44e1ec3830a81b5107a527a3bef224c022c0a","schema":1,"source_digest":"sha256:e6449194cbad54e3b3c68bc2efe44e1ec3830a81b5107a527a3bef224c022c0a","source_identity":"ticket:pi-multi-session-wayfinder/PMS-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 4: What to Build |
| acceptance | 5: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1926,"payload_sha256":"e6449194cbad54e3b3c68bc2efe44e1ec3830a81b5107a527a3bef224c022c0a","schema":1,"source_digest":"sha256:e6449194cbad54e3b3c68bc2efe44e1ec3830a81b5107a527a3bef224c022c0a","source_identity":"ticket:pi-multi-session-wayfinder/PMS-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "PMS-02"
execution_mode: AFK
blocked_by: []
---

# PMS-02 — Durable ticket claim across sessions

## Artifact Graph
- Artifact ID: `artifact:pi-multi-session-pms-02`
- Role: `ticket`
- Parent: [pi-multi-session-wayfinder.md](../../specs/pi-multi-session-wayfinder.md)

### Produces
- [Durable ticket claims across Pi sessions](../../research/pi-multi-session-claims.md)

## Parent Spec
[pi-multi-session-wayfinder.md](../../specs/pi-multi-session-wayfinder.md): Not Yet Specified (second item).

## What to Build
Research question: how should a session claim one ticket so that the other sessions see it and the
claim survives a crash, a compaction and a fresh session, without a scheduler? Compare at least:
Messenger `claim`/`unclaim` (swarm store), a `reserve` on the ticket file, and Git/provider state
(a pushed branch or draft PR named after the ticket). Expected output: a short research note
`docs/research/pi-multi-session-claims.md` that names this ticket as its source and recommends one
mechanism.

## Acceptance Criteria
- [ ] For each option: where the state lives, who can see it, what happens on crash, compaction,
      new session and stale claim, and how a claim is released.
- [ ] Facts come from the installed Messenger source and Git/provider behavior, with file
      references; untested behavior is marked as such.
- [ ] One recommendation with its known limits.

## Frontier
Done: see the research note.

## Step-by-Step Implementation Plan
1. Read the installed `pi-messenger` store and swarm handlers for claim storage and cleanup.
2. Check how a pushed branch or draft PR can be listed and matched to a ticket ID.
3. Write the comparison and recommendation.

## Testing Plan
Read-only research; optional throwaway checks in a temporary directory, recorded in the note.

## Out of Scope
- Implementing the claim or changing the skills (PMS-04).
- Crew task state.

```
