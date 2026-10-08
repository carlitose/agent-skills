---
name: crew-delivery
description: "Run several Pi agents on one repository like a human team: a PM writes spec and tickets, developers each work in their own Git worktree, a reviewer approves each branch, a merge queue is the only writer of main, and a cycle QA runs on the merged result. Use when a Crew (pi-messenger workers) or several Pi sessions already work on the same project by the user's decision, in any of these roles."
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
nothing is integrated. A human team avoids this with separate roles and one way into main.

## Roles

| Role | Does | Skills | Works in |
| --- | --- | --- | --- |
| PM | spec, tickets, assignment, merge queue; writes no product code | `to-spec`, `to-tickets` | own worktree; main only through the queue |
| Developer | one ticket at a time, code and tests | `execute-ticket` | own worktree and branch |
| Reviewer | review of each branch; cycle QA | `code-review`, `qa-test-plan` | read-only |

Nobody writes in the main folder. Install a `pre-commit` hook that refuses commits while the
current branch is `main`; the merge queue only fast-forwards, which needs no commit.

## Ticket cycle

1. **PM:** turn the request into a spec and tickets with `to-spec` and `to-tickets` on branch
   `crew/plan` in its worktree, and put it into main through the queue. A ticket is a whole
   slice of the request, closed by its own tests. Two tickets in flight never touch the same
   files; a change that touches everything is one ticket. Assign at most two tickets per
   developer per request, one at a time. Everything a role may do is in the ticket's `## Gates`:
   never make an agent wait for an acknowledgement during its work.
2. **Developer:** `git worktree add -b crew/<ticket-id> ../<repo-folder>-worktrees/<ticket-id> main`,
   then work only there. Carry the ticket with `execute-ticket` inline (skills-only) but skip its
   review stage: the reviewer owns it. Run the repository's tests, commit on the branch and
   deliver the branch name with the tests run. If it cannot be finished safely, stop and deliver
   the branch state and the concrete reason; do not retry with smaller pieces.
3. **Reviewer:** run `code-review` on `git diff main...crew/<ticket-id>` in that worktree, from a
   context separate from the developer's. Verdict: approved, or changes requested with findings.
   Changes go back to the same developer; the reviewer never edits; each changes-requested verdict
   counts as a block (step 5).
4. **Merge queue (PM, one branch at a time, no hand edits):** in the developer's worktree
   `git rebase main` (on conflict: `git rebase --abort`, the ticket goes back to its developer),
   run the repository's tests there, then `git -C <main-folder> merge --ff-only crew/<ticket-id>`,
   `git worktree remove` and delete the branch.
5. **Blocked ticket:** the PM does not finish it. It rewrites it as a clearer ticket, or joins it
   to another, and reassigns it. A second block on the same ticket stops the request, with the
   reason recorded.

## Cycle QA

When every ticket of the request is merged, the reviewer runs `qa-test-plan` and the full tests
on main. Every problem becomes a new ticket from the PM and goes through the same cycle. The
request is done only when QA passes on main: a developer's "done", green tests in a worktree or
a ticket file are not the result.

## Limits

- One shared resource (a database, a host, a long-running service) has one owner at a time:
  the PM, unless a ticket's `## Gates` assigns it to someone else.
- Reports between agents state facts with their evidence (command and result), not readiness.
