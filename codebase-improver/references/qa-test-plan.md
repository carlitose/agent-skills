# QA Test Plan — manual e2e checklist from the diff

Used by `quality-loop.md` Step 5. Produce a concrete, step-by-step **manual e2e test plan** a human (or the QA-simulate subagent) can execute against the running app. This is human-driven QA, **not** automated test code (the TDD tests in Step 2 cover that).

## Pipeline (in order)

### Phase 1 — Acquire the diff
The diff under review is the branch's change. Fetch with `git diff main...<branch>` (or `git diff HEAD` for uncommitted work).

### Phase 2 — Understand the change
For each modified file: what does the code do; what user-facing behavior it affects (UI flow, API response, side effect like email/DB write/job); what existing behavior it could break (regression risk); what new behavior should now exist (happy path). Read surrounding files, not just the hunks — a small change in a shared utility can have wide impact.

### Phase 3 — Map to surfaces
Translate changes into testable surfaces: UI flows (pages/forms/buttons), API endpoints (routes calling the changed code), CLI commands, background jobs/cron/queues, data written/read/migrated, side effects (emails, webhooks, external calls, file writes, logs). If a surface is unclear, grep callers up the stack until you reach a user-facing entry point.

### Phase 4 — Generate the plan
Markdown, these sections in order:

```markdown
# Test Plan — <short name of change>

## Scope
- One sentence: what this change does
- One sentence: how to verify it

## Prerequisites
- Environment (dev / staging / seed data), accounts/roles, feature flags, test data (e.g. "user with >5 orders")

## Happy Path
1. <concrete action> → <expected result>

## Edge Cases
1. <empty / null / boundary input> → <expected result>

## Negative / Error Paths
1. <invalid input> → <expected error / behavior>

## Regression Risks
Surfaces not directly changed but reachable from the changed code — verify they still work:
1. ...

## Out of Scope
What this change does NOT touch and does NOT need re-testing.
```

Each step must be **concrete** ("Click 'Submit'", not "submit the form"), **independently verifiable** (clear expected result), and **ordered** (prerequisites first).

## Output location

Save to `docs/qa/test-plan-<branch-or-hash>.md` (create `docs/qa/` if needed), so it can be attached to a PR or checked off. Print to chat instead if there's no writable repo.

## Large diffs (>~10 files or ~500 lines)

Don't produce one giant plan: group related changes (by feature/directory/concern), one section per group, list the groups at the top so testing can be parallelized.

## Anti-patterns

Vague steps; missing expected results; skipping regression (trace callers — a 5-line diff can break things 100 lines away); over-scoping (a label typo doesn't need a full checkout sweep); under-scoping (don't stop at the diff). Do not mix in automated test code here.
