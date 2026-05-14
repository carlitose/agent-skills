---
name: ralph
description: Run one autonomous AFK implementation iteration from local issue files. Use when the user asks Ralph to pick and complete the next AFK issue, continue work from docs/issues, process a change queue autonomously, or run a single issue-focused coding loop with tests, commit, and issue status updates.
---

# Ralph

Execute exactly one autonomous task from a local issue queue, using the current repo state, recent commits, and `docs/issues/<change-name>` as the source of truth.

Ralph is the queue runner. For a user-selected issue that should be executed directly without AFK queue selection, use the standalone `execute-issue` skill instead.

## Inputs

Expect the user or wrapper script to provide:

- Local issue files from `docs/issues/<change-name>`
- The last few commits, if available
- The repository working tree

If no actionable AFK issue remains, output exactly:

`<promise>NO MORE TASKS</promise>`

Do not search other `docs/issues/` change folders. Ralph is scoped to the provided `docs/issues/<change-name>` directory only, even if git status, recent commits, or repo exploration reveal other open issue folders.

## Issue Selection

Parse the issue files and work only on issues marked AFK or otherwise safe to complete without human interaction. Do not work on HITL issues.

If no root-level Markdown issue files are provided for the requested change, stop immediately with `<promise>NO MORE TASKS</promise>`.

The wrapper prompt must include the requested change name, the allowed issue directory, and the exact open issue file paths so the model has an explicit boundary.

Pick one task only. Prioritize in this order:

1. Critical bugfixes
2. Development infrastructure, including tests, types, build scripts, and local tooling
3. Tracer bullets for new features
4. Polish and quick wins
5. Refactors

A tracer bullet is a tiny end-to-end slice that passes through the main layers of the system so the architecture can be validated before expanding the feature.

## Workflow

### 1. Review context

Read the provided issue files and recent commits. Understand what has already been completed and which issue is the next best AFK task.

### 2. Explore the repo

Inspect the codebase enough to understand the implementation boundary, existing patterns, tests, and constraints. Do not enumerate or inspect other `docs/issues/` change folders as part of exploration.

### 3. Verify external docs

When working with a third-party framework, library, SDK, API, CLI, cloud service, endpoint, configuration option, or syntax, fetch current documentation using the repo's required documentation lookup flow before relying on API details.

If this workspace requires `ctx7`, use:

1. `npx ctx7@latest library <name> "<question>"`
2. `npx ctx7@latest docs <libraryId> "<question>"`

Do not use documentation lookup for general programming concepts or project-local business logic.

### 4. Implement with TDD

Use the repository's TDD workflow. Prefer behavior-focused tests at public boundaries over implementation-detail tests.

Keep the change scoped to the selected issue.

### 5. Run feedback loops

Before committing, run the relevant feedback loops. For .NET projects, default to:

- `dotnet build`
- `dotnet test`

If the repo is not a .NET project, infer the equivalent build, typecheck, lint, and test commands from existing project scripts and docs.

### 6. Commit

Update or move the issue file before committing. Then run `git status --short`, stage every task-related file, and make the commit as the last operation.

The commit message must include:

- Key decisions made
- Files changed
- Blockers or notes for the next iteration

After committing, run `git status --short` again. Do not finish with task-related modified, deleted, or untracked files outside the commit.

### 7. Update the issue

If the task is complete, move the issue file to:

`docs/issues/<change-name>/done/`

If the task is not complete, add a concise note to the issue file explaining what was done and what remains.

## Constraints

- Work on a single task only.
- Do not start HITL work.
- Do not continue into a second issue after committing.
- Do not skip tests unless blocked; if blocked, record the blocker in the issue and final response.
- Do not paste secrets from logs, prompts, or environment files.

## Optional Local Scripts

This skill directory may include shell wrappers used by the project:

- `ralph/once.sh <change-name> [model]`: run one Ralph pass with Claude.
- `ralph/afk.sh <iterations> <change-name> [model]`: run repeated Docker-backed Ralph passes until no tasks remain.
- `ralph/afk-nodock.sh <iterations> <change-name> [model]`: run repeated non-Docker Ralph passes.
- `ralph/once-codex.sh <change-name> [model]`: run one Ralph pass with Codex CLI.
- `ralph/afk-codex.sh <iterations> <change-name> [model]`: run repeated Codex CLI Ralph passes until no tasks remain.
- `ralph/afk-nodock-codex.sh <iterations> <change-name> [model]`: run repeated Codex CLI passes with approvals and sandboxing bypassed.

When acting as Codex inside this skill, follow the workflow above directly; do not invoke these scripts unless the user explicitly asks to run Ralph through the wrapper.
