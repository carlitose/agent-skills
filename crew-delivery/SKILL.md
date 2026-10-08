---
name: crew-delivery
description: "Coordinate several Pi agents on one repository so that work is finished, not just prepared: one Git worktree per worker, at most two whole tickets per worker, the coordinator integrates and tests the result. Use when a Crew (pi-messenger workers) or several Pi sessions already work on the same project by the user's decision, as coordinator or as worker."
---

# Crew Delivery

Owns: multi-agent coordination on one repository.

Use it only when the user has already set up several agents on one project (a pi-messenger
Crew, or several Pi sessions). It never creates delegation by itself: with one agent, work
serially inline as usual. The lane stays skills-only: no ticket-autopilot runner, scheduler or
driver.

Why: when several agents share one working tree, they overlap on the same files, find the
suite red because of a colleague's half-done change, split a change that touches everything
into pieces nobody can finish, and wait for acknowledgements. Everybody reports "ready" and
nothing is integrated. These rules remove those causes.

## Coordinator

1. Turn the request into a spec and tickets with `to-spec` and `to-tickets`, and commit them on
   `main` before any worker starts, so every worktree sees them.
2. Pick at most two tickets per worker per request. A ticket is a whole slice of the request,
   closed by its own tests. Two tickets in flight never touch the same files; a change that
   touches everything is one ticket, done by one agent (often you).
3. Create one worker task per ticket. The task names the ticket file, the worker's branch
   `crew/<ticket-id>` and its worktree folder `../<repo-folder>-worktrees/<ticket-id>`, outside
   the repository. Everything a worker may do is in the ticket's `## Gates`: never make a worker
   wait for an acknowledgement during its work.
4. Keep working on your own ticket while workers run; do not poll them for availability.
5. When a worker delivers its branch: merge it into `main` in the main folder, resolve any
   conflict yourself, run the repository's tests on the integrated result, then remove its
   worktree (`git worktree remove`) and branch.
6. A blocked task is not split again: read its reason and finish that ticket yourself in the
   main folder (or in its worktree, then integrate).
7. The request is done only when every ticket is integrated in `main` and the repository's
   tests and checks pass on `main`. A worker's "done", green tests in a worktree, or a ticket
   file are not the result.

## Worker

1. Create your worktree and branch from the current `main`:
   `git worktree add -b crew/<ticket-id> ../<repo-folder>-worktrees/<ticket-id> main`, and work
   only there. Never write in the main folder or in another worker's worktree.
2. Carry the ticket to the end with `execute-ticket` inline (skills-only): implementation, tests,
   review. Run the repository's tests in your worktree before delivering.
3. Commit on your branch and deliver its name and the tests you ran. Do not merge into `main`:
   the coordinator integrates.
4. If the ticket cannot be finished safely, stop and deliver the state of your branch and the
   concrete reason. Do not retry with smaller pieces.

## Limits

- One shared resource (a database, a host, a long-running service, the main folder) has one
  owner at a time: the coordinator, unless a ticket's `## Gates` assigns it to a worker.
- Reports between agents state facts with their evidence (command and result), not readiness.
