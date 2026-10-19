---
type: source
title: "Durable ticket claims across Pi sessions"
identity_key: artifact:pi-multi-session-claims
identity_strength: stable
source_path: docs/research/pi-multi-session-claims.md
source_digest: sha256:bcc849f25df9ccc448ddd7682dacccf6764b40e0c7028eb5eda980e300945e9f
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Durable ticket claims across Pi sessions

Compiled from `docs/research/pi-multi-session-claims.md`. Identity is `artifact:pi-multi-session-claims`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/ticket-pi-multi-session-wayfinder-pms-02]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"evidence":{"headings":[3],"status":"present"},"findings":{"headings":[],"status":"not-identified"},"limitations":{"headings":[],"status":"not-identified"},"method":{"headings":[],"status":"not-identified"},"question":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-pi-multi-session-claims.md","payload_bytes":3430,"payload_sha256":"bcc849f25df9ccc448ddd7682dacccf6764b40e0c7028eb5eda980e300945e9f"}],"payload_bytes":3430,"payload_sha256":"bcc849f25df9ccc448ddd7682dacccf6764b40e0c7028eb5eda980e300945e9f","schema":1,"source_digest":"sha256:bcc849f25df9ccc448ddd7682dacccf6764b40e0c7028eb5eda980e300945e9f","source_identity":"artifact:pi-multi-session-claims","source_kind":"research"} -->

| Topic | Source sections |
|---|---|
| question | no matching section identified in the source; complete source retained |
| method | no matching section identified in the source; complete source retained |
| findings | no matching section identified in the source; complete source retained |
| evidence | 3: Evidence |
| limitations | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3430,"payload_sha256":"bcc849f25df9ccc448ddd7682dacccf6764b40e0c7028eb5eda980e300945e9f","schema":1,"source_digest":"sha256:bcc849f25df9ccc448ddd7682dacccf6764b40e0c7028eb5eda980e300945e9f","source_identity":"artifact:pi-multi-session-claims"} -->
```markdown
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

```
