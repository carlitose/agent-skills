---
ticket_schema: 1
ticket_id: "PMS-01"
execution_mode: HITL
blocked_by: []
---

# PMS-01 — Live two-session Pi Messenger check on Windows

## Artifact Graph
- Artifact ID: `artifact:pi-multi-session-pms-01`
- Role: `ticket`
- Parent: [pi-multi-session-wayfinder.md](../../specs/pi-multi-session-wayfinder.md)

### Produces
- [Pi Messenger between live Pi sessions on Windows](../../research/pi-multi-session-messenger-live.md)

## Parent Spec
[pi-multi-session-wayfinder.md](../../specs/pi-multi-session-wayfinder.md): Not Yet Specified (first item).

## What to Build
Research question: do the Messenger primitives the protocol needs work between two live Pi
sessions on this native Windows host? Observe, do not assume. The human opens two Pi sessions in two
different worktrees of the same repository; the agent in each session runs the steps below.
Expected output: a short research note `docs/research/pi-multi-session-messenger-live.md` that
names this ticket as its source.

## Acceptance Criteria
- [ ] Both sessions `join` and see each other in `list` with their branch.
- [ ] A `send` from A wakes B with A's name, without B polling.
- [ ] A `reserve` by A blocks an `edit` by B on the same path with a message naming A; `release`
      unblocks it.
- [ ] `leave` and closing a session (and, if safe, killing it) release reservations; record how
      long dead-session cleanup takes.
- [ ] Whether reservations and the registry are scoped per repository or global is recorded.
- [ ] Every result is labeled observed, failed or not-run; nothing is inferred from the README.

## Frontier
Done: see the research note.

## Step-by-Step Implementation Plan
1. Create two disposable worktrees from `origin/main`; the human opens Pi in each.
2. Run join/list, send, reserve/edit/release, leave/close in that order, noting time and output.
3. Write the note with the observations and their limits; remove both worktrees.

## Testing Plan
Manual live check only; record the exact tool outputs. No automated test is added.

## Out of Scope
- Crew actions (`plan`, `work`, `task.*`, `team.*`).
- Fixing Messenger; failures are recorded and become new tickets.
