# ISSUES

Runtime context after these instructions provides the requested change name, allowed issue directory, and open issue files. Parse only those provided issue files to understand the open issues.

You will work on the AFK issues only, not the HITL ones.

Do not search `docs/issues/` for other changes. Do not switch to another issue folder when the requested change has no open issue files. Treat any other `docs/issues/...` path seen in git status, recent commits, search results, or codebase exploration as out of scope unless it is inside the allowed issue directory.

You've also been passed a file containing the last few commits. Review these to understand what work has been done.

If all AFK tasks for the requested change are complete, or if the runtime context says `Issues: No issues found`, output exactly <promise>NO MORE TASKS</promise> and do nothing else.

# TASK SELECTION

Pick the next task. Prioritize tasks in this order:

1. Critical bugfixes
2. Development infrastructure

Getting development infrastructure like tests and types and dev scripts ready is an important precursor to building features.

3. Tracer bullets for new features

Tracer bullets are small slices of functionality that go through all layers of the system, allowing you to test and validate your approach early. This helps in identifying potential issues and ensures that the overall architecture is sound before investing significant time in development.

TL;DR - build a tiny, end-to-end slice of the feature first, then expand it out.

4. Polish and quick wins
5. Refactors

# EXPLORATION

Explore the repo for code relevant to the provided issue only. Do not enumerate the issue queue. Do not run `find docs/issues`, `ls docs/issues`, or broad searches under `docs/issues`; only inspect the allowed issue directory provided at the start of context.

# DOCUMENTATION

Always use the **context7** skill to fetch up-to-date docs for any framework, library, or tech you're working with.

Never rely on memory for external APIs (Application Programming Interfaces), SDKs (Software Development Kits), endpoints, configuration options, or syntax — verify with context7 first.

**Rule:** If it's third-party, look it up.

# IMPLEMENTATION

Use /tdd to complete the task.

# FEEDBACK LOOPS

Before committing, run the feedback loops:

- `dotnet build` to compile the solution
- `dotnet test` to run the tests

# COMMIT

Make a git commit. The commit message must:

1. Include key decisions made
2. Include files changed
3. Blockers or notes for next iteration

# THE ISSUE

If the task is complete, move the issue file to the `done/` folder inside the allowed issue directory.

If the task is not complete, add a note to the issue file with what was done.

Only move or edit issue files under the allowed issue directory.

# FINAL RULES

ONLY WORK ON A SINGLE TASK.
