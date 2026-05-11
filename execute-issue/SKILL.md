---
name: execute-issue
description: Implement a specific issue end-to-end from a local issue file, pasted issue text, GitHub/Linear issue context, or existing conversation context. Use when the user asks to execute, implement, complete, resolve, or work through an issue without using an autonomous queue runner like Ralph.
---

# Execute Issue

Implement one specific issue from start to finish. This skill is intentionally independent from Ralph: it does not select from an AFK queue, run repeated iterations, or assume a wrapper script. It executes the issue the user gives you or the issue already present in context.

## Inputs

Accept any of these inputs:

- A local issue path, such as `docs/issues/<change>/<issue>.md`
- A folder of related local issue files, such as `docs/issues/<change>/`
- Pasted issue text
- A GitHub, Linear, or tracker issue already available in context
- A bug or task described in the current conversation

If the target issue is ambiguous, ask one concise question to identify it. If the issue is clear, proceed without asking.

## Process

### 1. Understand the issue

Read the issue and extract:

- The problem to solve
- Acceptance criteria
- Explicit non-goals
- Blockers, dependencies, or HITL requirements
- Expected tests or verification steps

If the issue is marked blocked or requires human input, stop and ask before implementing unless the user explicitly provided the missing decision.

### 2. Inspect current state

Explore the repo enough to verify the issue against reality:

- Existing behavior and failing tests, if any
- Nearby implementation patterns
- Public interfaces and boundaries affected by the change
- Existing tests that describe the behavior
- Project-specific commands in README, package scripts, CI config, Makefile, task files, or solution files

Keep exploration proportional to the issue. Do not refactor unrelated code.

### 3. Check current external documentation

For third-party frameworks, libraries, SDKs, APIs, CLI tools, cloud services, endpoints, configuration options, or syntax, fetch current documentation using the repository's required documentation lookup flow.

In repositories that require `ctx7`, use:

1. `npx ctx7@latest library <name> "<specific question>"`
2. `npx ctx7@latest docs <libraryId> "<specific question>"`

Do not use external documentation lookup for general programming concepts or project-local business logic.

### 4. Implement with focused tests

Prefer test-first work when practical:

- Reproduce the issue with a failing test, or identify an existing failing test
- Implement the smallest coherent change that satisfies the issue
- Keep tests at public boundaries where possible
- Avoid implementation-detail assertions unless the project already uses them for this layer

If the issue is too small for a new test, state why in the final response.

### 5. Verify

Run the most relevant feedback loops before finishing:

- Targeted tests for the changed behavior
- Broader test suite if the change touches shared behavior
- Build, typecheck, lint, or format commands expected by the repo

If a command cannot run because of missing services, dependencies, credentials, or sandbox restrictions, record the blocker clearly.

### 6. Update the issue record

If the issue came from a local Markdown file:

- Move it to `done/` only when acceptance criteria are met and verification has run or the blocker is explicitly acceptable.
- If incomplete, append a short progress note with completed work, verification status, and remaining blockers.

If the issue came from a tracker and tracker tools are available, update the tracker only if the user asked you to. Otherwise, summarize what should be posted.

### 7. Commit when appropriate

Commit only when the user requested commits or the issue workflow clearly expects commits.

When committing, include:

- What changed
- Key decisions
- Tests or verification run
- Remaining blockers, if any

Do not include unrelated untracked files.

## Final Response

Report:

- What was implemented
- Files changed
- Verification run and results
- Issue update or remaining blocker

Keep the response concise. Do not paste large diffs.
