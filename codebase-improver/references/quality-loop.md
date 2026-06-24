# Quality Loop — TDD + review + QA for implementing an RFC

How Stage 3.6 implements a chosen RFC: **test-driven**, heavy steps delegated to **subagents**, iterating until clean. The main agent is the orchestrator — it sequences the steps, holds the iteration counter and git state, and keeps the HITL gates. It writes as little code itself as possible.

This loop is **self-contained**: reviewers use this skill's own catalogs (`universal-checks.md`, `audit-catalog.md`) as the rubric. It does not call any external review/QA skill.

## Not AFK

Unlike an unattended autopilot, this loop is HITL. It runs the steps below to completion and then reports — it does not prompt mid-loop — but it **never fabricates a human-gate decision**. If a step hits something only a human can decide (an ambiguous behavior change, a blocked dependency, a destructive or out-of-scope action), it stops that branch, records why, and surfaces it. Git side-effects beyond creating a local branch + commit (push, PR, merge) always wait for explicit go-ahead.

## Configuration

Read from the SKILL.md config block; defaults: `MAX_QUALITY_ITERATIONS=3`, `REVIEW_BLOCKING_SEVERITY=high`, `GIT_STRATEGY=branch`.

## The loop

### Step 1 — Branch
`git switch -c improve/<rfc-slug>`. Confirm with the user first. Never push/PR/merge here.

### Step 2 — Tests first (red)  ·  subagent
Spawn a test-writer subagent. It writes tests at the **deepened module's interface boundary**, derived from the RFC's acceptance criteria and the behavior to preserve:
- **Behavior-preserving refactor** → characterization tests that capture current behavior; they should pass before and after.
- **New behavior** → failing tests that specify the target (true TDD red).

Per `deep-module-reference.md`: assert on observable outcomes through the public interface, not internal state. Run the tests so the red/green baseline is explicit.

### Step 3 — Implement (green)  ·  subagent
Spawn an implementer subagent. It makes the tests pass in small, behavior-preserving steps, applying `simplify-playbook.md` (explicit over clever, even if longer). Return: files changed, commands run + results, whether acceptance is met, any blocker.

A hard blocker (missing credential, unreachable service, needs a human decision) → stop the branch, record it, exit the loop as "blocked".

### Step 4 — Review (parallel)  ·  two subagents in one batch
Spawn two reviewers in the same turn against the uncommitted diff, each following `review-rubric.md`:
- **Reviewer 1 — Correctness (recall-biased).** The 8-angle scan + verify pass (`review-rubric.md` §Reviewer 1). Returns ≤10 findings ranked by severity. Supplement with `universal-checks.md` for secrets/risky calls.
- **Reviewer 2 — Maintainability (thermo-nuclear).** The ambitious code-judo / 1k-line / anti-spaghetti / approval-bar standards (`review-rubric.md` §Reviewer 2). Supplement with `audit-catalog.md`. Also confirm the diff actually *deepens* the module (interface shrank, complexity moved inside).

Merge and dedupe per the rubric's merge step. Keep findings at `REVIEW_BLOCKING_SEVERITY`+ as **blocking** (Reviewer 2's presumptive blockers count as `high` unless justified); record the rest without blocking.

### Step 5 — QA plan + simulate  ·  two subagents
- **QA-plan subagent**: produce a concrete, ordered e2e checklist following `qa-test-plan.md` (Scope, Prerequisites, Happy Path, Edge Cases, Negative/Error, Regression Risks, Out of Scope). Save to `docs/qa/test-plan-<branch>.md`.
- **QA-simulate subagent**: execute/simulate each step against the code and, where feasible, the running app/tests. Return `{step, pass|fail|skipped, evidence}`. Do **not** guess a pass; if a step can't be exercised here, mark it `skipped` with the reason.

### Step 6 — Decide & loop
- **Clean** = no blocking review findings remain AND all QA steps pass (skips allowed only for genuinely un-runnable steps) → go to Step 7.
- **Not clean** → spawn a fix subagent (preserve behavior, re-run tests/build/lint), then **return to Step 4** on the new diff. Increment the iteration counter.
- **Counter hits `MAX_QUALITY_ITERATIONS`** → stop. Leave the diff on the branch, mark "needs human", record the unresolved findings/QA failures, exit.

### Step 7 — Finalize
- Confirm tests are green and the module is genuinely deeper (interface smaller than before).
- `GIT_STRATEGY=branch`: commit with a message summarizing what changed, tests run, review + QA status. **PR/push only on explicit user go-ahead. Never auto-merge.**
- Report (skimmable): files changed, test result, review summary (blocking vs recorded), QA result, and any autonomous decisions the user should review.

## Subagent notes

- Give each subagent the RFC path, the relevant prior results, and a required structured-output shape so you can branch on it (not prose).
- Spawn independent steps in one message (the two reviewers; the two QA subagents if the plan is fixed).
- Subagents are scoped to *this* RFC's diff — they don't touch other modules.
- The orchestrator never lets the loop run past the iteration cap silently, and never performs a prohibited/irreversible git action without the user.
