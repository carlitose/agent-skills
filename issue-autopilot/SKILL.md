---
name: issue-autopilot
description: Autonomously drive a whole folder of local issue files to done — for each ready issue it runs execute-issue, then code-review + thermo-nuclear-code-quality-review, fixes findings, generates a qa-test-plan, simulates the QA, fixes any failures, and loops until clean, then moves on respecting the dependency DAG. Runs AFK (no human prompts) and delegates every heavy step to subagents. Use when the user wants to "do the whole issue folder until everything is in done", run an AFK issue loop, or autopilot a PRD's issues.
---

# Issue Autopilot

Take a folder of local Markdown issue files (the output of `prd-to-issues`) and drive **every issue that can be done** to `done/`, autonomously and AFK. For each issue you run a full quality loop — implement → review → fix → QA → simulate → fix — and you keep going, in dependency order, until the folder is exhausted or only human-gated work remains.

**Delegate aggressively to subagents.** The main thread is the *orchestrator*: it builds the plan, picks the next issue, spawns subagents for the expensive work (implementation, review, fixing, QA, QA-simulation), reads their structured results, and decides what happens next. The main thread does as little file-editing itself as possible.

## AFK contract (non-negotiable)

This skill runs unattended. Therefore:

- **Never call `AskUserQuestion`** and never block waiting on the user. When a real decision is needed, make the best defensible choice, record it, and continue.
- **Never fabricate a human gate decision.** Issues that are inherently HITL (a go/no-go gate, an architectural sign-off, a design approval) cannot be "decided" by the autopilot. Produce the *deliverable* the issue asks for (e.g. write the memo with a recommendation), but if downstream issues are blocked by a human decision (e.g. "only if go"), stop that branch, flag it, and move to other ready work.
- **Fail forward.** One issue blocked or failing must not abort the whole run. Skip it with a recorded reason and continue with the rest of the ready set.
- Track progress with `TaskCreate`/`TaskUpdate` so the user can see live state when they return.

## Inputs

- **Argument (optional):** a path to an issue folder, e.g. `docs/issues/<change>/`.
- **Default if no argument:** `docs/issues/consumer-deepseek-migration/`.

Accept either an absolute path or one relative to the repo root. Resolve it once at the start.

## Configuration (defaults chosen for AFK safety)

These are defaults. If the user's invocation overrides one in plain language, honor it.

- **`GIT_STRATEGY` = `branch-pr`** — for each completed issue, create a branch, commit, and open a PR with `gh`. **Do NOT auto-merge** (this repo auto-deploys on merge to `main`, so auto-merging would ship to prod unattended). Alternatives: `commit-main` (commit straight to main — deploys to prod, only if user explicitly asks), `worktree-only` (implement + move to done/, leave changes uncommitted for human review).
- **`MAX_QUALITY_ITERATIONS` = `3`** — max review→fix→QA cycles per issue before giving up and flagging the issue as "needs human".
- **`REVIEW_BLOCKING_SEVERITY` = `high`** — only findings at this severity or above block an issue from reaching done; lower findings are recorded in the PR/notes but don't block.

## Running this AFK with `/goal` (recommended)

This skill does the work; the built-in `/goal` command is the AFK engine that keeps re-invoking it across turns until the folder is exhausted. Pair them:

```
/goal every non-done issue in docs/issues/<change>/ has either been moved to done/ or recorded as blocked-needs-human, then run /issue-autopilot docs/issues/<change>/
```

`/goal` evaluates the completion condition after each turn with a fast model and auto-continues if it is not met, so nobody has to prompt between iterations. The completion condition MUST let human-gated issues count as "settled" (moved to `done/` **or** flagged blocked) — otherwise `/goal` loops forever waiting on a decision only a human can make. Clear it any time with `/goal clear`.

If invoked without `/goal`, the skill still runs its own outer loop within a single turn; `/goal` just extends that across turns for large folders.

## Process

### Phase 0 — Build the work graph (orchestrator, do this yourself)

1. Resolve the target folder. List `*.md` files in it (NOT recursing into `done/`).
2. The `done/` subfolder is the source of truth for completion: any issue already in `done/` is finished.
3. For each pending issue, parse its `## Blocked by` section. Extract referenced issue filenames. An issue is **ready** when every blocker is already in `done/`.
4. Detect HITL/gate issues: an issue whose acceptance is a human decision (go/no-go, sign-off), or whose blockers carry a conditional like "(post-gate: solo se 'go')" / "only if go". Mark these so the loop handles them specially.
5. Create one task per pending issue with `TaskCreate`. Log the computed ready set and the blocked set with `log`-style notes in your response.

If the folder has no pending issues, report "all done" and stop.

### Phase 1 — Outer loop (orchestrator)

Repeat until no ready issue remains:

1. Pick the **lowest-numbered ready issue** (numbers encode dependency order).
2. Mark its task `in_progress`.
3. Run the **per-issue quality loop** (Phase 2) for that single issue.
4. On success: confirm the file was moved to `done/`, handle git per `GIT_STRATEGY`, mark the task `completed`, recompute the ready set (newly-unblocked issues become available).
5. On block/failure: mark the task with the reason, leave the file in place, and **continue** with the next ready issue. Do not retry the same issue more than `MAX_QUALITY_ITERATIONS` total.

Stop conditions:
- All issues are in `done/` → success.
- The only remaining pending issues are blocked by an unmet **human gate** or by other blocked issues → stop and report the gate.

### Phase 2 — Per-issue quality loop (delegate every step to subagents)

For the chosen issue, run this loop. Each lettered step is a **separate subagent** spawned via the `Agent` tool. Pass each subagent the issue path and the relevant prior results; require structured output so you can branch on it.

**a. Implement** — one subagent (`general-purpose`).
> Prompt: "Invoke the `execute-issue` skill to implement ONLY this issue end-to-end: `<issue-path>`. Follow the repo's quality gates (tests, build, lint, typecheck where they apply). Do not touch other issues. Return: files changed, commands run + results, whether acceptance criteria are met, and any blocker."

If the subagent reports a hard blocker (missing credential, blocked-by human input, unreachable service), record it and **exit this loop** as "blocked" — do not move to done/.

**b. Review** — two subagents **in parallel** (one message, two `Agent` calls).
> Reviewer 1: "Invoke the `code-review` skill on the current branch's uncommitted diff. Return findings as a list of {severity, file:line, problem, suggested fix}."
> Reviewer 2: "Invoke the `thermo-nuclear-code-quality-review` skill on the current branch's changes. Return the same structured findings shape."

Merge and dedupe findings. Keep only those at `REVIEW_BLOCKING_SEVERITY`+ as blocking.

**c. Fix review findings** — one subagent (`general-purpose`), only if there are blocking findings.
> Prompt: "Apply these review findings to the working tree, preserving behavior. Re-run the relevant tests/build/lint after. Findings: <list>. Return what changed and verification results."

**d. Generate QA plan** — one subagent.
> Prompt: "Invoke the `qa-test-plan` skill against the current uncommitted diff. Produce a concrete step-by-step manual e2e checklist. Return it as an ordered list of steps, each with the action and the expected observable result."

**e. Simulate the QA (AFK)** — one subagent (`general-purpose`).
> Prompt: "You are the QA executor running AFK — no human is available. Execute/simulate each step of this QA checklist against the code and, where feasible, the running app/tests. For each step return {step, pass|fail, evidence}. Do not guess a pass: if a step truly cannot be exercised AFK, mark it `skipped` with the reason. Checklist: <steps>."

**f. Decide & loop.**
- If all QA steps pass (skips allowed for genuinely human-only steps) and no blocking review findings remain → **issue is clean**. Proceed to step g.
- If there are QA failures or remaining blocking findings → spawn a **fix subagent** (same shape as c, fed the failures) and go back to **step b** (re-review the new diff). Increment the iteration counter.
- If the counter hits `MAX_QUALITY_ITERATIONS` → stop, mark the issue "needs human", leave the diff in place, record the unresolved items, and exit the loop without moving to done/.

**g. Finalize the issue.**
- Ensure the issue file is in `done/` (execute-issue normally does this; if not, move it).
- Apply `GIT_STRATEGY`: for `branch-pr`, create branch `autopilot/<issue-slug>`, commit (message summarizing what changed, tests run, review/QA status), push, `gh pr create`. Never auto-merge.
- Mark the task `completed`.

### HITL / gate issues

When the chosen issue is a gate (e.g. `*-go-no-go-memo.md`):

1. Still produce its deliverable AFK — implement the analysis/memo with a clear, evidence-backed **recommendation** (e.g. "recommend GO because …"), and satisfy any acceptance criterion that is just "the memo is written".
2. Move it to `done/` only if its acceptance criteria are purely "produce the artifact" (not "a human decided").
3. For downstream issues gated on the *decision* (the "only if go" branch), **do not assume the outcome**. Mark them `blocked: awaiting human gate decision` and skip. Surface this prominently in the final report so the user can make the call and re-run the autopilot to clear that branch.

## Final report

When the run stops, report concisely:

- Issues moved to `done/` this run, each with its PR link (if `branch-pr`).
- Issues flagged "needs human" and why (gate decision, repeated QA failure, hard blocker).
- The remaining dependency state: what's now ready, what's still blocked and by what.
- Any decisions you made autonomously that the user should review.

Do not paste large diffs. Keep it skimmable — the user was AFK and needs the state at a glance.

## Notes on subagent usage

- Spawn independent steps in a single message (parallel) when they don't depend on each other — notably the two reviewers in step b.
- Give each subagent a `schema` expectation in the prompt so it returns parseable structured data, not prose.
- Subagents CAN invoke skills via the Skill tool — that's how `execute-issue`, `code-review`, `thermo-nuclear-code-quality-review`, and `qa-test-plan` get run inside them. Tell them the exact skill name.
- The orchestrator keeps the small, stateful decisions (graph, ready set, counters, git); it should not itself be writing implementation code.
- For very large folders, consider running the per-issue loops of *independent* ready issues concurrently — but only when their file footprints don't overlap, to avoid merge conflicts. When unsure, serialize.
