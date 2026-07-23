---
name: "ticket-autopilot"
description: "AFK ticket loop with focused code simplification, review, QA, and verified explanatory GitHub PR bodies."
---

# Ticket Autopilot

Take a folder of local Markdown ticket files, usually the output of `to-tickets`, and drive every ticket that can be done to `done/`. For each ready ticket, run a full quality loop:

`implement -> simplify -> review -> fix -> QA -> simulate -> fix -> open PR -> explain PR`

Continue in dependency order until the folder is exhausted or only human-gated work remains.

Delegate aggressively to subagents. The main thread is the orchestrator: it builds the plan, picks the next ticket, spawns subagents for expensive work, reads their structured results, and decides what happens next. The main thread should do as little file editing itself as possible.

## AFK contract

This skill runs unattended.

- Never block waiting on the user. When a real decision is needed, make the best defensible choice only if it is safe to do so, record it, and continue.
- Never fabricate a human gate decision. Tickets that require sign-off, go/no-go, architecture approval, design approval, credentials, or other human input cannot be decided by the autopilot.
- Fail forward. One blocked or failing ticket must not abort the whole run.
- Track progress with the host task/progress tool so the user can see state when they return.

## Inputs

- **Argument, optional:** a path to a ticket folder, e.g. `docs/tickets/<change>/`.
- **Default if no argument:** ask for the folder unless the current context contains one unambiguous ticket folder.

Accept either an absolute path or one relative to the repo root. Resolve it once at the start.

## Configuration

Defaults chosen for AFK safety:

- **`GIT_STRATEGY` = `branch-pr`**: for each completed ticket, create a branch, commit, and open a PR with `gh`. Do not auto-merge.
- **`MAX_QUALITY_ITERATIONS` = `3`**: maximum review/fix/QA cycles per ticket before flagging it as needing a human.
- **`REVIEW_BLOCKING_SEVERITY` = `high`**: only findings at this severity or above block a ticket from reaching `done/`.
- **`CODE_SIMPLIFICATION_SKILL` = `code-simplification`**: after implementation, simplify only the current ticket's changed code while preserving behavior and verification evidence.
- **`PR_EXPLANATION_SKILL` = `explain-pr`**: after opening or locating the PR, update its real GitHub body with a plain-language explanation and exactly one evidence-based Mermaid diagram.

If the user's invocation overrides one in plain language, honor it.

## Running this AFK with `/goal`

This skill does the work. The built-in `/goal` command can keep re-invoking it across turns until the folder is exhausted:

```text
/goal every non-done ticket in docs/tickets/<change>/ has either been moved to done/ or recorded as blocked-needs-human, then run /ticket-autopilot docs/tickets/<change>/
```

The completion condition must let human-gated tickets count as settled once they are recorded as blocked; otherwise the goal loop waits forever for a decision only a human can make.

## Process

### Phase 0: Build the work graph

1. Resolve the target folder. List `*.md` files in it, excluding `done/`.
2. Treat `done/` as the source of truth for completion.
3. For each pending ticket, parse `## Blocked By` and extract referenced ticket filenames.
4. A ticket is ready when every blocker is already in `done/`.
5. Detect HITL/gate tickets: human sign-off, go/no-go, design approval, credentials, or a blocker that depends on a human decision.
6. Create one task per pending ticket. Log the ready set and blocked set.

If the folder has no pending tickets, report "all done" and stop.

### Phase 1: Outer loop

Repeat until no ready ticket remains:

1. Pick the lowest-numbered ready ticket.
2. Mark its task `in_progress`.
3. Run the per-ticket quality loop.
4. On success: confirm the file is in `done/`, handle git and the PR explanation according to `GIT_STRATEGY`, mark the task `completed`, and recompute the ready set.
5. On block or failure: mark the task with the reason, leave the file in place, and continue with the next ready ticket.

Stop when all tickets are in `done/`, or when the only remaining tickets are blocked by a human gate or by another blocked ticket.

### Phase 2: Per-ticket quality loop

For the chosen ticket, run these steps. Each step should be a separate subagent unless the host cannot delegate.

**a. Implement**

Prompt:

> Invoke the `execute-ticket` skill to implement ONLY this ticket end-to-end: `<ticket-path>`. Follow the repo's quality gates. Do not touch other tickets. Return: files changed, commands run and results, whether acceptance criteria are met, and any blocker.

If the subagent reports a hard blocker, record it and exit this loop as blocked.

**b. Simplify the implementation**

Prompt:

> Invoke the `code-simplification` skill on ONLY the current ticket's implementation diff. Preserve behavior, public contracts, errors, side effects, ordering, concurrency behavior, performance constraints, and existing tests. Follow repository conventions. Do not perform unrelated cleanup and do not modify tests to make a refactor pass. Return the structured simplification result and verification evidence.

Handle the result as follows:

- `simplified`: retain the changes only when the reported tests or checks support behavior preservation.
- `no-op`: continue normally; no useful simplification is a valid outcome.
- `blocked`: discard only the attempted simplification changes and continue reviewing the original implementation when it remains valid. If the blocker exposes a failure in the implementation itself, record it as an implementation blocker instead.

Do not let a failed optional cleanup corrupt or hide a working implementation. Re-run `code-simplification` after review fixes only when those fixes introduced meaningful new complexity; do not loop it mechanically.

**c. Review**

Run two reviewers in parallel:

- Reviewer 1 invokes the `code-review` skill on the current branch's uncommitted diff.
- Reviewer 2 invokes the strict maintainability review expected by this repo, if available.

Require findings as `{severity, file:line, problem, suggested_fix}`. Merge and dedupe findings. Keep only findings at `REVIEW_BLOCKING_SEVERITY` or above as blocking.

**d. Fix review findings**

If blocking findings exist, spawn a fix subagent:

> Apply these review findings to the working tree, preserving behavior. Re-run the relevant tests, build, or lint checks. Return what changed and verification results.

**e. Generate QA plan**

Spawn a QA-plan subagent:

> Invoke the `qa-test-plan` skill against the current uncommitted diff. Produce a concrete step-by-step manual end-to-end checklist. Return ordered steps with action and expected observable result.

**f. Simulate QA**

Spawn a QA executor:

> Execute or simulate each QA step AFK against the code and, where feasible, the running app or tests. For each step return `{step, pass|fail|skipped, evidence}`. Do not guess a pass.

**g. Decide and loop**

- If QA passes or is skipped only for genuinely human-only steps, and no blocking review findings remain, the ticket is clean.
- If QA fails or blocking findings remain, spawn a fix subagent and return to review.
- If the counter reaches `MAX_QUALITY_ITERATIONS`, mark the ticket as needing a human, leave the diff in place, record unresolved items, and move on.

**h. Finalize and open PR**

- Ensure the ticket file is in `done/`; `execute-ticket` normally does this.
- Apply `GIT_STRATEGY`. For `branch-pr`, create `autopilot/<ticket-slug>`, commit, push, and open a PR. Never auto-merge.
- Capture the PR URL or number plus the ticket path, acceptance criteria, changed-file summary, simplification result, review results, executed commands, test/build/lint results, QA evidence, skipped checks, and known risks. This is the evidence bundle for the PR explanation.

**i. Explain and verify the PR**

For `branch-pr`, invoke `explain-pr` against the PR just opened or found. Pass the evidence bundle from step h.

Required result:

- The real GitHub PR body is created or updated, not merely returned as local Markdown.
- It explains what changed, why, before versus after, the changed code, how the new flow works, verification, risks, and reviewer checks in language understandable by a technically curious 15-year-old.
- It contains exactly one useful GitHub-compatible Mermaid diagram derived from the diff and surrounding code.
- It preserves relevant human-written PR context and replaces stale generated sections rather than duplicating them.

After the update, read the PR back with `gh pr view` and verify:

1. All required `explain-pr` headings are present.
2. Exactly one Mermaid code block is present.
3. Verification claims match the captured evidence.
4. The PR URL matches the current ticket branch.

If PR mutation or verification fails, retry once after refreshing the PR and authentication state. If it still fails, do not mark the task completed: record the exact blocker as `blocked-needs-human`, include the generated Markdown body in the structured result, and continue with the next ready ticket.

Only after the GitHub body passes verification may the task be marked `completed`.

## HITL / Gate Tickets

When the chosen ticket is a gate, still produce any deliverable that can be produced AFK, such as a recommendation memo. Move it to `done/` only if its acceptance criteria are purely artifact production. For downstream tickets gated on the human decision, do not assume the outcome. Mark them `blocked: awaiting human gate decision` and skip.

## Final Report

Report concisely:

- Tickets moved to `done/` this run, with PR links if applicable.
- For every ticket, whether code simplification changed the implementation or was a no-op, plus its verification status.
- For every PR, whether its explanatory GitHub body and Mermaid diagram were verified.
- Tickets flagged as needing a human and why.
- Remaining dependency state: ready, blocked, and blocker.
- Autonomous decisions the user should review.

Do not paste large diffs or full PR bodies.

## Notes on Subagent Usage

- Spawn independent steps in parallel when they do not depend on each other, especially reviewers.
- Give each subagent a structured output schema.
- Subagents can invoke skills via the host Skill tool. Use the exact names: `execute-ticket`, `code-simplification`, `code-review`, `qa-test-plan`, and `explain-pr`.
- For very large folders, independent ready tickets can run concurrently only when their file footprints do not overlap. When unsure, serialize.
