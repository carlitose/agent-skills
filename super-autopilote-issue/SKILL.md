---
name: super-autopilote-issue
description: >-
  Variante autosuficiente de issue-autopilot. Conduce AFK una carpeta de issues locales a done/,
  ejecutando por cada issue un ciclo completo implementar (con TDD estricto) → review → fix → QA →
  simular → fix, en orden de dependencias. NO depende de skills locales del repo: la lógica de
  implementación, el ciclo red-green-refactor, el review thermo-nuclear y la generación del plan de QA
  van inlineadas en los subagentes. La única dependencia externa es la code-review nativa de Claude Code.
  Úsala cuando quieras autopilotar una carpeta de issues a done sin requerir que existan execute-issue /
  thermo-nuclear-code-quality-review / qa-test-plan / tdd.
---

# Super Autopilote Issue

Take a folder of local Markdown issue files (the output of a PRD-to-issues breakdown) and drive **every issue that can be done** to `done/`, autonomously and AFK. For each issue you run a full quality loop — implement (test-driven) → review → fix → QA → simulate → fix — and you keep going, in dependency order, until the folder is exhausted or only human-gated work remains.

**This skill is self-contained.** Unlike `issue-autopilot`, it does **not** depend on any repo-local skill. The logic of implementation, the strict red-green-refactor TDD loop, the thermo-nuclear quality review, and the QA-plan generation are all **inlined into the subagent prompts below** — the subagents do NOT invoke `execute-issue`, `thermo-nuclear-code-quality-review`, `qa-test-plan`, or `tdd`. The **only** external skill it uses is the **`code-review` skill that ships natively with Claude Code**.

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
/goal every non-done issue in docs/issues/<change>/ has either been moved to done/ or recorded as blocked-needs-human, then run /super-autopilote-issue docs/issues/<change>/
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

For the chosen issue, run this loop. Each lettered step is a **separate subagent** spawned via the `Agent` tool. Pass each subagent the issue path and the relevant prior results; require structured output so you can branch on it. **The implementation, thermo-nuclear review, and QA-plan steps carry their full instructions inline — do NOT tell the subagent to "invoke a skill" for those.** Only the first reviewer uses the native `code-review` skill.

**a. Implement with strict TDD (red-green-refactor)** — one subagent (`general-purpose`). Pass it the issue path and the full instructions below verbatim:

> Implement ONLY this issue end-to-end: `<issue-path>`. Do not touch other issues. Work test-driven. Follow exactly this process:
>
> 1. **Understand the issue.** Extract: the problem to solve, acceptance criteria, explicit non-goals, blockers/dependencies/HITL requirements, and expected tests or verification steps. If the issue is marked blocked or requires human input you cannot supply, STOP and return that blocker — do not guess a human decision.
> 2. **Inspect current state.** Explore the repo enough to verify the issue against reality: existing behavior and failing tests, nearby implementation patterns, public interfaces and boundaries affected, existing tests describing the behavior, and project-specific commands (README, package scripts, CI config, Makefile, task files). Keep exploration proportional to the issue; do not refactor unrelated code.
> 3. **Check external docs.** For third-party frameworks, libraries, SDKs, APIs, CLI tools, or cloud services, fetch current documentation using the repo's required lookup flow. In this repo use `ctx7`: `npx ctx7@latest library <name> "<question>"` then `npx ctx7@latest docs <libraryId> "<question>"`. Do not use it for general programming concepts or project-local business logic.
> 4. **Implement in vertical slices (tracer bullets), NEVER horizontal.** Derive the list of behaviors to test from the issue's acceptance criteria yourself — you are running AFK, so do NOT ask anyone to approve the plan. Then, for each behavior, run one red-green cycle:
>    - **RED:** write ONE test that fails. The test must exercise the **public interface** and describe **behavior, not implementation** (it should survive an internal refactor). Confirm it fails.
>    - **GREEN:** write the **minimal** code to make that one test pass. Do not anticipate future tests. Confirm it passes.
>    - Repeat for the next behavior. One test at a time. Do NOT write all tests first then all implementation.
>    - **Never refactor while a test is RED** — get to green first.
> 5. **Refactor (only once green).** Extract duplication, deepen modules (push complexity behind simple interfaces), apply SOLID where natural. Run the tests after each refactor step. Per-cycle checklist: test describes behavior not implementation; test uses public interface only; test survives internal refactor; code is minimal; no speculative features.
> 6. **Verify.** Run the most relevant feedback loops: targeted tests for the changed behavior, the broader suite if the change touches shared behavior, plus build/typecheck/lint/format commands the repo expects. If a command cannot run (missing services, deps, credentials, sandbox limits), record the blocker clearly — do not pretend it passed.
> 7. **Update the issue record.** If acceptance criteria are met and verification ran, move the `.md` file to `done/`. If incomplete, append a short progress note (work done, verification status, remaining blockers) and leave it in place.
> 8. **Return structured output:** `{files_changed, commands_run_and_results, acceptance_criteria_met (bool), blocker (string or null)}`. Keep prose minimal; do not paste large diffs.

If the subagent reports a hard blocker (missing credential, blocked-by human input, unreachable service), record it and **exit this loop** as "blocked" — do not move to done/.

**b. Review** — two subagents **in parallel** (one message, two `Agent` calls).
> Reviewer 1 (uses the native skill): "Invoke the `code-review` skill on the current branch's uncommitted diff. Return findings as a list of `{severity, file:line, problem, suggested_fix}`."
> Reviewer 2 (instructions inline — do NOT invoke any skill): pass it the prompt below.
>
> > Perform a deep, extremely strict code-quality audit of the current branch's uncommitted changes. Return findings as a list of `{severity, file:line, problem, suggested_fix}` using the same shape as the other reviewer. Apply these standards:
> >
> > - **Be ambitious about structural simplification.** Don't stop at "this could be cleaner." Look for "code judo" moves: behavior-preserving restructurings that make whole branches, helpers, modes, conditionals, or layers disappear. Prefer deleting complexity over rearranging it. Prefer the solution that makes the code feel inevitable in hindsight.
> > - **File-size smell:** treat a PR pushing a file from under 1k lines to over 1k lines as a strong code-quality smell. Prefer extracting helpers/subcomponents/modules. Only waive with a compelling structural reason and a still-clearly-organized result.
> > - **No spaghetti growth:** be highly suspicious of new ad-hoc conditionals, scattered special cases, or one-off branches bolted into unrelated flows. Push logic into a dedicated abstraction/helper/state machine/policy object instead of tangling an existing path.
> > - **Clean the design, don't just accept working code.** If behavior can stay the same while structure becomes meaningfully cleaner, push for the cleaner version. Prefer removing moving pieces over spreading the same complexity around.
> > - **Prefer direct, boring, maintainable code over hacky/magical code.** Flag thin abstractions, identity wrappers, pass-through helpers, and generic mechanisms that hide simple data-shape assumptions.
> > - **Type and boundary cleanliness:** question unnecessary optionality, `any`/`unknown`, or cast-heavy code when a clearer type boundary could exist. Flag silent fallbacks that paper over unclear invariants.
> > - **Canonical layer & reuse:** call out feature logic leaking into shared paths or implementation details leaking through APIs. Prefer existing canonical utilities over bespoke near-duplicates. Push code toward the package/module that already owns the concept.
> > - **Orchestration:** flag unnecessary sequential orchestration of independent work, and non-atomic updates that can leave state half-applied, when a cleaner structure is obvious.
> >
> > Prioritize: structural regressions > missed dramatic-simplification opportunities > spaghetti/branching increases > boundary/type-contract problems > file-size/decomposition > modularity > legibility. Don't flood with low-value nits when larger structural issues exist; prefer a few high-conviction findings. Be direct and demanding about quality, but not rude.

Merge and dedupe findings from both reviewers. Keep only those at `REVIEW_BLOCKING_SEVERITY`+ as blocking.

**c. Fix review findings** — one subagent (`general-purpose`), only if there are blocking findings.
> Prompt: "Apply these review findings to the working tree, preserving behavior. Re-run the relevant tests/build/lint after. Findings: <list>. Return what changed and verification results."

**d. Generate QA plan (instructions inline — do NOT invoke any skill)** — one subagent.
> Prompt: "Produce a concrete step-by-step **manual end-to-end test plan** a human could execute against the running application, based on the current uncommitted diff. This is for human-driven QA, not automated test code. Follow this pipeline:
>
> 1. **Acquire the diff.** Default to `git diff HEAD` (the uncommitted working-tree changes).
> 2. **Understand the change.** For each modified file: what the code does; what user-facing behavior it affects (UI flow, API response, side effect, background job); what existing behavior could break (regression risk); what new behavior should now exist (happy path). Read surrounding files, not just the hunks — a small diff in a shared utility can have wide impact.
> 3. **Map to surfaces.** Translate code changes into testable surfaces: UI flows, API endpoints, CLI commands, background jobs/cron/queues, data written/read/migrated, side effects (emails, webhooks, external calls, file writes, logs). If a surface is unclear, trace callers up the stack with Grep until you reach a user-facing entry point.
> 4. **Write the plan** with these sections in order: `## Scope` (one line what + one line how-to-verify), `## Prerequisites` (env, accounts/roles, feature flags, test data), `## Happy Path`, `## Edge Cases`, `## Negative / Error Paths`, `## Regression Risks` (surfaces not directly changed but reachable), `## Out of Scope`. Every step must be concrete (\"Click 'Submit'\" not \"submit the form\"), independently verifiable (has a clear expected result), and ordered (prerequisites first). Keep the plan proportional to the change — don't over- or under-scope.
>
> Return the plan as an ordered list of steps, each as `{step, action, expected_result}`."

**e. Simulate the QA (AFK)** — one subagent (`general-purpose`).
> Prompt: "You are the QA executor running AFK — no human is available. Execute/simulate each step of this QA checklist against the code and, where feasible, the running app/tests. For each step return `{step, pass|fail, evidence}`. Do not guess a pass: if a step truly cannot be exercised AFK, mark it `skipped` with the reason. Checklist: <steps>."

**f. Decide & loop.**
- If all QA steps pass (skips allowed for genuinely human-only steps) and no blocking review findings remain → **issue is clean**. Proceed to step g.
- If there are QA failures or remaining blocking findings → spawn a **fix subagent** (same shape as c, fed the failures) and go back to **step b** (re-review the new diff). Increment the iteration counter.
- If the counter hits `MAX_QUALITY_ITERATIONS` → stop, mark the issue "needs human", leave the diff in place, record the unresolved items, and exit the loop without moving to done/.

**g. Finalize the issue.**
- Ensure the issue file is in `done/` (step a normally does this; if not, move it).
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
- This skill is self-contained: the implementation (step a, with its TDD loop), the strict quality review (reviewer 2 in step b), and the QA-plan (step d) carry their **full instructions inline** — subagents must NOT invoke any repo-local skill for those. The **only** skill invocation allowed is the native **`code-review`** in reviewer 1 of step b; tell that subagent the exact skill name.
- The orchestrator keeps the small, stateful decisions (graph, ready set, counters, git); it should not itself be writing implementation code.
- For very large folders, consider running the per-issue loops of *independent* ready issues concurrently — but only when their file footprints don't overlap, to avoid merge conflicts. When unsure, serialize.
