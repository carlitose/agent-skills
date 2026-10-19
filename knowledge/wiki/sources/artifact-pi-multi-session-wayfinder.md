---
type: source
title: "Pi multi-session work with Pi Messenger"
identity_key: artifact:pi-multi-session-wayfinder
identity_strength: stable
source_path: docs/specs/pi-multi-session-wayfinder.md
source_digest: sha256:995b450d042a440ea837ec15528397927d31a80b97c696ad1ad2e39b0b60333c
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Pi multi-session work with Pi Messenger

Compiled from `docs/specs/pi-multi-session-wayfinder.md`. Identity is `artifact:pi-multi-session-wayfinder`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/artifact-pi-multi-session-protocol]]
- Child source: [[sources/ticket-pi-multi-session-wayfinder-pms-01]]
- Child source: [[sources/ticket-pi-multi-session-wayfinder-pms-02]]
- Child source: [[sources/ticket-pi-multi-session-wayfinder-pms-03]]
- Child source: [[sources/ticket-pi-multi-session-wayfinder-pms-04]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[6],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"goals":{"headings":[5],"status":"present"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-pi-multi-session-wayfinder.md","payload_bytes":3615,"payload_sha256":"995b450d042a440ea837ec15528397927d31a80b97c696ad1ad2e39b0b60333c"}],"payload_bytes":3615,"payload_sha256":"995b450d042a440ea837ec15528397927d31a80b97c696ad1ad2e39b0b60333c","schema":1,"source_digest":"sha256:995b450d042a440ea837ec15528397927d31a80b97c696ad1ad2e39b0b60333c","source_identity":"artifact:pi-multi-session-wayfinder","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | 5: Destination |
| exclusions | 8: Out of Scope |
| decisions | 6: Decisions So Far |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3615,"payload_sha256":"995b450d042a440ea837ec15528397927d31a80b97c696ad1ad2e39b0b60333c","schema":1,"source_digest":"sha256:995b450d042a440ea837ec15528397927d31a80b97c696ad1ad2e39b0b60333c","source_identity":"artifact:pi-multi-session-wayfinder"} -->
```markdown
# Pi multi-session work with Pi Messenger

## Artifact Graph
- Artifact ID: `artifact:pi-multi-session-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children
- [Pi multi-session protocol (decisions)](pi-multi-session-protocol.md)
- [PMS-01 live two-session Messenger check](../tickets/pi-multi-session-wayfinder/01-live-two-session-check.md)
- [PMS-02 durable ticket claim](../tickets/pi-multi-session-wayfinder/02-durable-ticket-claim.md)
- [PMS-03 coordination protocol decisions](../tickets/pi-multi-session-wayfinder/03-protocol-decisions.md)
- [PMS-04 protocol in the skills](../tickets/pi-multi-session-wayfinder/04-protocol-in-skills.md)

## Type
Wayfinding spec

## Status
Complete

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
- Protocol confirmed in PMS-03 ([decisions](pi-multi-session-protocol.md)): a main Pi updates the
  map, orders and performs merges under human authority and cleans up; workers claim tickets
  themselves with Messenger `claim` on the main-checkout spec path (not a Git branch, human
  choice); short English messages `CLAIMED`/`READY`/`BLOCKED`/`DONE`; `.pi/messenger/` ignored.
- After a PR is merged or closed, its worktree is always removed (user request, 2026-10-05); the
  rule is written into the skills by PMS-04.

## Not Yet Specified
- Live check (PMS-01, [research](../research/pi-multi-session-messenger-live.md)): messages,
  wake-up, `leave` and dead-session cleanup work on Windows; reservations match only the literal
  path and are bypassed by an absolute path. Messenger writes `.pi/messenger/` into the repo.
- Whether a Messenger claim survives `/reload` and compaction in a live session (expected from
  the code, not observed).

## Out of Scope
- Crew planning or work waves, subagents, spawned workers, Autopilot.
- Remote or cross-machine sessions, Redis, authenticated messaging.
- Changing pi-messenger itself or its version pin.

## Frontier / Blocking Edges
- None.

## Ticket Plan
- PMS-01, research, HITL, no blockers: live two-session check; output a research note.
- PMS-02, research, AFK, no blockers: durable claim options from Messenger code and Git/provider
  state; output a research note with a recommendation.
- PMS-03, grilling, HITL, blocked by PMS-01 and PMS-02: confirm the protocol; output a decision spec.
- PMS-04, task, AFK, blocked by PMS-03: write the protocol and the worktree-removal rule into the
  skills; output a skills change with tests.

## Next Review
All tickets done. Open: observe a Messenger claim across two live sessions and after `/reload`.

```
