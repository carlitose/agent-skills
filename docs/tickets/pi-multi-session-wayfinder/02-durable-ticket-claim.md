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
Ready.

## Step-by-Step Implementation Plan
1. Read the installed `pi-messenger` store and swarm handlers for claim storage and cleanup.
2. Check how a pushed branch or draft PR can be listed and matched to a ticket ID.
3. Write the comparison and recommendation.

## Testing Plan
Read-only research; optional throwaway checks in a temporary directory, recorded in the note.

## Out of Scope
- Implementing the claim or changing the skills (PMS-04).
- Crew task state.
