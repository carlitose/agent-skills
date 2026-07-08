---
name: super-autopilote-ticket
description: Self-contained AFK variant of ticket-autopilot. Drives a local ticket folder to done with inline implementation, strict TDD, review, QA planning, QA simulation, and fixes, without depending on repo-local execution skills.
---

# Super Autopilote Ticket

Take a folder of local Markdown ticket files and drive every ticket that can be done to
`done/`, autonomously and AFK. This is the self-contained variant of `ticket-autopilot`:
the implementation loop, strict TDD discipline, maintainability review, and QA-plan
generation are inlined into the subagent prompts. Subagents do not invoke repo-local
skills such as `execute-ticket`, `qa-test-plan`, or `tdd`. The only review skill it may
invoke is `code-review` when available; otherwise use the inline review prompt.

For each ready ticket, run:

`implement with TDD -> review -> fix -> QA plan -> simulate QA -> fix`

Continue in dependency order until the folder is exhausted or only human-gated work
remains.

## AFK contract

This skill runs unattended.

- Never block waiting on the user.
- Never fabricate a human gate decision. Sign-off, go/no-go, architecture approval,
  design approval, credentials, and external access gates remain human-gated.
- Fail forward. One blocked or failing ticket must not abort the whole run.
- Track progress with the host task/progress tool so the user can see state when they
  return.

## Inputs

- **Argument, optional:** a path to a ticket folder, e.g. `docs/tickets/<change>/`.
- **Default if no argument:** ask for the folder unless the current context contains one
  unambiguous ticket folder.

Accept either an absolute path or one relative to the repo root. Resolve it once at the
start.

## Configuration

- **`GIT_STRATEGY` = `branch-pr`**: create a branch, commit, and open a PR per completed
  ticket. Do not auto-merge.
- **`MAX_QUALITY_ITERATIONS` = `3`**: maximum review/fix/QA cycles per ticket before
  flagging it as needing a human.
- **`REVIEW_BLOCKING_SEVERITY` = `high`**: only findings at this severity or above block a
  ticket from reaching `done/`.

Honor explicit user overrides.

## Running this AFK with `/goal`

```text
/goal every non-done ticket in docs/tickets/<change>/ has either been moved to done/ or recorded as blocked-needs-human, then run /super-autopilote-ticket docs/tickets/<change>/
```

The completion condition must let human-gated tickets count as settled once they are
recorded as blocked.

## Process

### Phase 0: Build the work graph

1. Resolve the target folder. List `*.md` files in it, excluding `done/`.
2. Treat `done/` as the source of truth for completion.
3. Parse each pending ticket's `## Blocked By` section and extract referenced filenames.
4. A ticket is ready when every blocker is already in `done/`.
5. Detect HITL/gate tickets: human sign-off, go/no-go, design approval, credentials, or a
   blocker that depends on a human decision.
6. Create one task per pending ticket and log the ready/blocked sets.

If the folder has no pending tickets, report "all done" and stop.

### Phase 1: Outer loop

Repeat until no ready ticket remains:

1. Pick the lowest-numbered ready ticket.
2. Mark its task `in_progress`.
3. Run the per-ticket quality loop below.
4. On success: confirm the file is in `done/`, handle git according to `GIT_STRATEGY`,
   mark the task `completed`, and recompute the ready set.
5. On block or failure: mark the task with the reason, leave the file in place, and
   continue with the next ready ticket.

Stop when all tickets are in `done/`, or when the remaining tickets are blocked by a
human gate or another blocked ticket.

### Phase 2: Per-ticket quality loop

Each step is a separate subagent unless the host cannot delegate. Require structured
outputs so the orchestrator can branch reliably.

#### a. Implement with strict TDD

Pass this prompt to one implementation subagent:

> Implement ONLY this ticket end-to-end: `<ticket-path>`. Do not touch other tickets.
> Work test-driven and return structured output:
> `{files_changed, commands_run_and_results, acceptance_criteria_met, blocker}`.
>
> 1. Read the ticket and extract the problem, acceptance criteria, non-goals, blockers,
>    frontier state, and verification expectations. If it requires human input you cannot
>    supply, stop and return the blocker.
> 2. Inspect the repo enough to verify current behavior, affected public boundaries,
>    nearby patterns, relevant tests, and project commands. Keep scope tight.
> 3. For third-party APIs or frameworks, use the repo's required documentation lookup
>    flow. Do not fetch docs for project-local business logic.
> 4. Implement in vertical slices, not horizontal layers. For each behavior:
>    - RED: write one failing test through a public boundary.
>    - GREEN: write the minimal code to pass that one test.
>    - Repeat for the next behavior.
>    - Never refactor while a test is red.
> 5. Refactor only once green. Push complexity behind clear interfaces, remove duplication,
>    and keep behavior unchanged. Re-run tests after each refactor step.
> 6. Verify with targeted tests and broader build/typecheck/lint/format checks where
>    relevant. Record missing services, credentials, dependencies, or sandbox blockers.
> 7. If acceptance criteria are met and verification ran, move the ticket file to `done/`.
>    If incomplete, append a progress note and leave it in place.

If the subagent reports a hard blocker, record it and exit this loop as blocked.

#### b. Review

Run two reviewers in parallel:

- Reviewer 1 invokes the native `code-review` skill on the uncommitted diff.
- Reviewer 2 performs the inline strict maintainability review below.

Reviewer 2 prompt:

> Perform a strict maintainability audit of the current uncommitted changes. Return
> findings as `{severity, file:line, problem, suggested_fix}`. Prioritize structural
> regressions, missed simplifications, tangled branching, unclear type boundaries,
> duplication, canonical-layer violations, and risky orchestration. Prefer a few
> high-conviction findings over low-value nits.

Merge and dedupe findings. Keep only findings at `REVIEW_BLOCKING_SEVERITY` or above as
blocking.

#### c. Fix review findings

If blocking findings exist, spawn a fix subagent:

> Apply these review findings while preserving behavior. Re-run the relevant tests, build,
> or lint checks. Return changed files and verification results.

#### d. Generate QA plan

Spawn a QA-plan subagent with inline instructions:

> Produce a concrete manual end-to-end test plan from the current uncommitted diff.
> Understand the changed behavior, map it to user-facing surfaces, identify prerequisites,
> happy paths, edge cases, negative paths, regression risks, and out-of-scope areas. Return
> ordered steps as `{step, action, expected_result}`.

#### e. Simulate QA

Spawn a QA executor:

> Execute or simulate each QA step AFK against the code and, where feasible, the running
> app or tests. For each step return `{step, pass|fail|skipped, evidence}`. Do not guess a
> pass.

#### f. Decide and loop

- If QA passes or is skipped only for genuinely human-only steps, and no blocking review
  findings remain, the ticket is clean.
- If QA fails or blocking findings remain, spawn a fix subagent and return to review.
- If the counter reaches `MAX_QUALITY_ITERATIONS`, mark the ticket as needing a human,
  leave the diff in place, record unresolved items, and move on.

#### g. Finalize

- Ensure the ticket file is in `done/`.
- Apply `GIT_STRATEGY`. For `branch-pr`, create `autopilot/<ticket-slug>`, commit, push,
  and open a PR. Never auto-merge.
- Mark the task `completed`.

## HITL / Gate Tickets

When the chosen ticket is a gate, produce any deliverable that can be produced AFK, such
as a recommendation memo. Move it to `done/` only if acceptance criteria are purely
artifact production. For downstream tickets gated on the human decision, do not assume the
outcome. Mark them `blocked: awaiting human gate decision` and skip.

## Final Report

Report concisely:

- Tickets moved to `done/` this run, with PR links if applicable.
- Tickets flagged as needing a human and why.
- Remaining dependency state: ready, blocked, and blocker.
- Autonomous decisions the user should review.

Do not paste large diffs.

