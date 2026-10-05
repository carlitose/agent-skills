# Pi multi-session work with Pi Messenger

## Artifact Graph
- Artifact ID: `artifact:pi-multi-session-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children
- [PMS-01 live two-session Messenger check](../tickets/pi-multi-session-wayfinder/01-live-two-session-check.md)
- [PMS-02 durable ticket claim](../tickets/pi-multi-session-wayfinder/02-durable-ticket-claim.md)
- [PMS-03 coordination protocol decisions](../tickets/pi-multi-session-wayfinder/03-protocol-decisions.md)
- [PMS-04 protocol in the skills](../tickets/pi-multi-session-wayfinder/04-protocol-in-skills.md)

## Type
Wayfinding spec

## Status
Active

## Destination
The human opens several Pi sessions by hand. Each session delivers a different ticket of the same
spec or Wayfinder map in the skills-only lane, in its own worktree, and the sessions stay
coordinated through Pi Messenger. Repository files (map, tickets, PRs) remain the source of truth;
Messenger messages and reservations only announce and protect, they never decide.

## Decisions So Far
- Sessions are opened by the human, never by another session: no Crew, no subagents, no runner or
  scheduler (user answer, 2026-10-05; operating defaults on delegation; `always-skills-only`).
- Messenger is `pi-messenger@0.15.2`, bundled by pi-personal-config #61 without the Crew skill and
  with `autoRegister: false`. Its state is file-based (`~/.pi/agent/messenger/`, project
  `.pi/messenger/`); messages wake the receiver as a steering prompt; `reserve` blocks other
  sessions' `edit`/`write` through a `tool_call` hook.
- Peer messages are not human approvals and are not authenticated: any local writer of the inbox
  can forge them (pi-personal-config spec `pi-messenger-bundle`, invariant 4).
- After a PR is merged or closed, its worktree is always removed (user request, 2026-10-05); the
  rule is written into the skills by PMS-04.

## Not Yet Specified
- Live check (PMS-01, [research](../research/pi-multi-session-messenger-live.md)): messages,
  wake-up, `leave` and dead-session cleanup work on Windows; reservations match only the literal
  path and are bypassed by an absolute path. Messenger writes `.pi/messenger/` into the repo.
- Claim mechanism: PMS-02 recommends a non-force push of a branch named after the ticket ID;
  Messenger `claim`/`reserve` miss the same ticket across worktrees and drop on crash
  ([research](../research/pi-multi-session-claims.md)). To be confirmed in PMS-03.
- Who updates the shared map, in which order PRs touching the same files are merged, and which
  message conventions the sessions use (PMS-03).

## Out of Scope
- Crew planning or work waves, subagents, spawned workers, Autopilot.
- Remote or cross-machine sessions, Redis, authenticated messaging.
- Changing pi-messenger itself or its version pin.

## Frontier / Blocking Edges
- The protocol decisions block the skill text; unblocked by PMS-03 confirmation.

## Ticket Plan
- PMS-01, research, HITL, no blockers: live two-session check; output a research note.
- PMS-02, research, AFK, no blockers: durable claim options from Messenger code and Git/provider
  state; output a research note with a recommendation.
- PMS-03, grilling, HITL, blocked by PMS-01 and PMS-02: confirm the protocol; output a decision spec.
- PMS-04, task, AFK, blocked by PMS-03: write the protocol and the worktree-removal rule into the
  skills; output a skills change with tests.

## Next Review
PMS-01 and PMS-02 done. Next: PMS-03 grilling with the human.
