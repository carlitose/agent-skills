# Durable ticket claims across Pi sessions

## Artifact Graph
- Artifact ID: `artifact:pi-multi-session-claims`
- Role: `research`
- Parent: [PMS-02 durable ticket claim](../tickets/pi-multi-session-wayfinder/02-durable-ticket-claim.md)

## Answer

Use Git as the claim: a session claims a ticket by pushing a new branch named after the ticket ID
(for example `pms-02-<slug>`) without force, before any other work. The remote accepts only the
first push of a new branch name, survives crashes, compactions and new sessions, and every session
can list it. Messenger only announces the claim (`send`/`broadcast`); it is not the claim. The
claim ends when the PR is merged or closed: GitHub deletes the remote branch on merge here, and the
session removes its worktree and local branch.

Messenger's own `claim` and `reserve` do not fit sessions that each work in their own worktree,
because both compare paths that differ between worktrees.

## Evidence

Installed `pi-messenger@0.15.2` (`pi-personal-config/node_modules/pi-messenger`):

- `store.ts` `claimTask`: claims live in the global `~/.pi/agent/messenger/claims.json`, keyed by
  spec path then task ID, one claim per agent, written atomically under `swarm.lock`.
- `lib.ts` `resolveSpecPath`: a relative spec path is resolved against the session's cwd, so
  `docs/specs/x.md` in `C:/wt-a` and in `C:/wt-b` become two different keys; two worktrees can
  both "claim" the same ticket.
- `store.ts` `isClaimStale`: a claim is dropped when its process is dead or the registration's
  session ID changed. A crash or a new session loses the claim; it is a lock, not a record.
- `lib.ts` `pathMatchesReservation`: a reservation matches only the identical string (or a prefix
  ending in `/`); `index.ts` checks it against the raw `path` of `edit`/`write` only. A reservation
  made in one worktree does not match the same file in another worktree, and `bash` writes are not
  checked.
- `index.ts`: all state is under `PI_MESSENGER_DIR` or `~/.pi/agent/messenger`, global to the user,
  not per repository.

Git and GitHub:

- Throwaway check (temporary bare repository, two clones): both created `claim/PMS-02`; the first
  push succeeded, the second was rejected `(fetch first)` and the remote kept the first commit.
- `gh api repos/carlitose/agent-skills` reports `delete_branch_on_merge: true`.

| Option | Where it lives | Seen by | Crash / compaction / new session | Same ticket in two worktrees |
|---|---|---|---|---|
| Messenger `claim` | global `claims.json` | sessions that joined | lost (stale on dead PID or new session ID) | not detected (absolute path keys differ) |
| Messenger `reserve` on the ticket file | registry entry of the session | sessions that joined | released | not detected (literal path match) |
| Pushed branch named after the ticket | remote repository | everyone (`git ls-remote`, `gh pr list`) | kept | second push rejected |

## Unknowns

- Live Windows behavior of Messenger messages and dead-session cleanup is PMS-01; none of the above
  was observed in two live sessions.
- A branch whose session died stays claimed until a human deletes it; stale detection (for example
  last commit date) is a PMS-03 decision.
- Branch naming for the claim must be fixed in PMS-03 (ticket ID as prefix is assumed here).

## Next Step

PMS-03 confirms the claim rule above with the human, together with the map-update and merge-order
rules, after PMS-01.
