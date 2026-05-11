---
name: qa-test-plan
description: Use this skill whenever the user wants a step-by-step end-to-end (e2e) test plan generated from code changes. Trigger on any input that represents a change — a git commit, a pull request (PR), unstaged or staged working changes, a branch diff, a specific file, a pasted diff/patch, or even a verbal description of what changed. Trigger phrases include "test plan", "QA plan", "how do I test this", "what should I check", "manual test steps", "e2e test plan", "QA this commit/PR", "regression test for these changes", "what flows are affected", "give me a checklist". Use this even when the user does not say "skill" — the goal is to convert a code delta into a concrete checklist a human can execute against the running application. Do NOT use this skill if the user is asking for *automated* test code (Playwright, Jest, pytest, etc.) — that is a different task.
---

# QA Test Plan Generator (from code changes)

Given any code change — commit, PR, unstaged file, branch diff, pasted patch, or verbal description — produce a concrete step-by-step **manual end-to-end test plan** that a human can execute against the running application.

This is for **human-driven QA**, not for generating automated test code. The output is a checklist of things to click, type, observe, and verify in the actual app.

## When to use vs when to skip

- **Use** when the user wants to know what to test, what could break, or wants a pre-deploy / pre-merge checklist.
- **Skip** when the user is asking you to *write automated tests*. Test plans are for humans; automated tests are code.

If unclear, ask once: *"Manual test plan to run yourself, or automated tests in code?"*

## Pipeline

Run these phases in order. Do not skip ahead to writing the plan before understanding the diff.

### Phase 1 — Acquire the diff

Figure out what changed. The user's input determines the source:

| Input | How to fetch |
|---|---|
| Commit hash | `git show <hash>` |
| Two refs | `git diff <base>..<head>` |
| Branch vs main | `git diff main...<branch>` |
| PR number / URL | `gh pr diff <number>` (or GitHub MCP if connected) |
| Unstaged | `git diff` |
| Staged | `git diff --staged` |
| Everything in working tree | `git status` then `git diff HEAD` |
| Specific file (new) | `cat <path>` |
| Specific file (modified) | `git log -p -- <path>` |
| Pasted patch | use directly |
| Verbal description | ask one clarifying question, then proceed |

If the user is ambiguous ("test the changes"), default to `git diff HEAD` and confirm: *"Testing your uncommitted changes — is that right?"*

### Phase 2 — Understand the change

For each modified file, answer:

1. **What does this code do?** (the function, endpoint, component, migration)
2. **What user-facing behavior does it affect?** — UI flow, API response, side effect (email, DB write, file output), background job
3. **What existing behavior could it break?** — regression risk
4. **What new behavior should now exist?** — happy path expectation

Read the surrounding files (not just the diff hunks) for context. A small diff in a shared utility can have wide impact.

### Phase 3 — Map to surfaces

Translate code changes into testable surfaces:

- **UI flows** — which pages, screens, forms, or buttons are reachable from the changed code?
- **API endpoints** — which HTTP routes call the changed code?
- **CLI commands** — which commands invoke it?
- **Background jobs / cron / queues** — any async triggers?
- **Data** — what gets written, read, or migrated?
- **Side effects** — emails, webhooks, external API calls, file writes, logs

If the surface is unclear, use Grep to trace callers up the call stack until you reach a user-facing entry point.

### Phase 4 — Generate the test plan

Produce a markdown plan with these sections, in this order:

```markdown
# Test Plan — <short name of change>

## Scope
- One sentence: what this change does
- One sentence: how to verify it

## Prerequisites
- Environment (dev / staging / specific seed data)
- Accounts / roles needed
- Feature flags to enable
- Test data required (e.g., "user with >5 orders")

## Happy Path
1. <concrete action> → <expected result>
2. ...

## Edge Cases
1. <empty / null / boundary input> → <expected result>
2. ...

## Negative / Error Paths
1. <invalid input> → <expected error message / behavior>
2. ...

## Regression Risks
Surfaces not directly changed but reachable from the changed code — verify they still work:
1. ...

## Out of Scope
What this change does NOT touch and does NOT need re-testing.
```

Each step must be:

- **Concrete** — "Click the 'Submit' button" not "submit the form"
- **Independently verifiable** — has a clear expected result
- **Ordered** — prerequisites first, dependent steps after

If a step needs specific data, say so explicitly in Prerequisites or inline in the step.

## Output format

By default, save the plan to a markdown file:

- `qa/test-plan-<branch-or-hash>.md` if a `qa/` directory exists
- Otherwise `test-plan-<branch-or-hash>.md` in the repo root

This makes it easy to share with reviewers, attach to a PR, or check off items as the human runs through them.

Print to chat instead if the user prefers ephemeral output, or if there is no writable repo (e.g., they only pasted a diff). Ask once if unclear.

## Example

**Input:** commit that adds rate limiting to the login endpoint.

**Output excerpt:**

```markdown
## Happy Path
1. POST /login with valid credentials, 1 request → 200 OK, session cookie set
2. POST /login with valid credentials, 5 requests within 1 minute → all 200 OK

## Edge Cases
1. POST /login 6th time within 1 minute → 429 Too Many Requests, `Retry-After` header present
2. Wait 60s after rate limit → next request → 200 OK

## Negative / Error Paths
1. POST /login with wrong password → 401 Unauthorized, attempt counted toward rate limit
2. POST /login with malformed JSON → 400 Bad Request, attempt NOT counted

## Regression Risks
1. /logout still works (shares the auth middleware)
2. Password reset flow still works (also writes to login_attempts table)
3. SSO login path still works (bypasses rate limiter — verify it still does)
```

## Anti-patterns to avoid

- **Vague steps** — "Test the login" is not a step. "Open /login, type a valid email and password, click 'Sign in', expect redirect to /dashboard" is.
- **Missing expected results** — every step must have a verification, otherwise it is not a test.
- **Skipping regression** — a 5-line diff can break things 100 lines away. Always trace callers.
- **Mixing in automated test code** — this skill produces a plan for a human. If the user wants automated tests too, deliver them as a separate file and label them clearly.
- **Over-scoping** — do not add steps for things the diff does not touch. The plan should be proportional to the change. A typo fix in a button label does not need a regression sweep of the whole checkout.
- **Under-scoping** — do not stop at the diff. Look at what calls the changed code.

## When the diff is large

If the diff touches more than ~10 files or ~500 lines, do not produce one giant plan. Instead:

1. Group related changes (by feature, by directory, by concern)
2. Produce one section per group
3. List the groups at the top so the human can parallelize testing

Ask the user if they want to prioritize one group first.
