# Pi multi-session protocol

## Artifact Graph
- Artifact ID: `artifact:pi-multi-session-protocol`
- Role: `spec`
- Parent: [pi-multi-session-wayfinder.md](pi-multi-session-wayfinder.md)

## Type
Decision spec. Decisions confirmed by the human in the PMS-03 interview (2026-10-05), from the
findings of [PMS-01](../research/pi-multi-session-messenger-live.md) and
[PMS-02](../research/pi-multi-session-claims.md).

## Roles
- **Main Pi**: one session in the main checkout. It updates the map, decides merge order, asks a
  worker to rebase when two PRs touch the same files, merges only under the human's merge
  authority, then removes the worker's worktree and local branch and announces the result.
- **Workers**: sessions the human opens by hand, each in its own worktree. A worker claims one ticket
  by itself, delivers it in the skills-only lane, opens the PR and reports to the main Pi. Workers do
  not edit the map and do not merge.

No session opens another session: no Crew, subagents, runner or scheduler.

## Rules
1. **Join.** Every session runs `pi_messenger join`; `autoRegister` stays off.
2. **Pick.** A worker takes the lowest-numbered ticket of the map that is not done, not claimed or
   completed in Messenger (`swarm`), and whose blockers are `DONE`.
3. **Claim.** It calls Messenger `claim` with the spec path **of the main checkout** (absolute) and
   the ticket ID, so every worktree uses the same key. If the claim is refused, it picks the next
   ticket. If a worktree or branch for that ticket already exists, it stops and asks the main Pi.
4. **Messages** are short and in English:

   | From | Message | When |
   |---|---|---|
   | Worker | `CLAIMED 03` | after the claim |
   | Worker | `READY 03 PR #415` | PR open, checks green; then Messenger `complete` |
   | Worker | `BLOCKED 03: <reason>` | a decision or input is needed |
   | Main Pi | `DONE 03` | after merge and cleanup |

5. **Authority.** A peer message is never a human approval and is not authenticated. A decision a
   worker cannot take goes worker → main Pi → human.
6. **Reservations are not protection.** `reserve` matches only the literal path string, so it does
   not protect files across worktrees or absolute paths; do not rely on it.
7. **Cleanup.** After a PR is merged or closed, its worktree and local branch are always removed and
   the main checkout is fast-forwarded. A worker that gives up a ticket calls `unclaim`.
   Messenger allows one claim per session, so `complete` at `READY` frees the worker for the next
   ticket; Messenger does not refuse a new claim on a completed ticket, hence the check in rule 2.
8. **Messenger files.** `.pi/messenger/` is ignored by Git.

## Known limits
- A claim is dropped when its session dies or a new session replaces it (`isClaimStale` in the
  installed `store.ts`); rule 3's existing-worktree check covers the lost work. By the same code a
  `/reload` or compaction keeps the claim (same process and session ID); not observed live.
- Claim behavior across two live sessions was not observed; PMS-01 observed messages, `leave`,
  crash cleanup and the reservation bypass.

## Implementation
PMS-04 writes these rules into the skills (short text: the Autopilot context budget has 64 bytes of
margin) and adds the always-remove-worktree rule. This change already adds `.pi/messenger/` to
`.gitignore`.
