---
name: "execute-ticket"
description: "Implement one ticket end-to-end; backward compatibility and legacy shims are opt-in."
---

# Execute Ticket

Implement one specific ticket from start to finish. This skill does not choose from a
queue. It executes the ticket the user gives you, or the ticket already present in
context.

## Backward compatibility default

Unless the ticket, spec, or user explicitly requires backward compatibility, implement the
clean target state. Do not preserve legacy APIs, aliases, configuration keys, formats, or
code paths through shims or parallel implementations by default. Treat compatibility as
an explicit acceptance criterion, not an inferred obligation. Still protect data integrity
and report breaking external contracts or irreversible migrations clearly.

## Inputs

Accept any of these inputs:

- A local ticket path, such as `docs/tickets/<change>/<ticket>.md`.
- A folder of related local ticket files, such as `docs/tickets/<change>/`.
- Pasted ticket text.
- A GitHub, Linear, or tracker ticket already available in context.
- A bug or task described in the current conversation.

If the target ticket is ambiguous, ask one concise question to identify it. If the ticket
is clear, proceed without asking.

## Process

### 1. Understand the ticket

Read the ticket and extract:

- The problem to solve.
- Acceptance criteria.
- Explicit non-goals.
- Blockers, dependencies, frontier state, or HITL requirements.
- Expected tests or verification steps.

If the ticket is marked blocked or requires human input, stop and ask before implementing
unless the user explicitly provided the missing decision.

### 2. Inspect current state

Explore the repo enough to verify the ticket against reality:

- Existing behavior and failing tests, if any.
- Nearby implementation patterns.
- Public interfaces and boundaries affected by the change.
- Existing tests that describe the behavior.
- Project-specific commands in README, package scripts, CI config, Makefile, task files,
  or solution files.

Keep exploration proportional to the ticket. Do not refactor unrelated code.

### 3. Check current external documentation

For third-party frameworks, libraries, SDKs, APIs, CLI tools, cloud services, endpoints,
configuration options, or syntax, fetch current documentation using the repository's
required documentation lookup flow.

In repositories that require `ctx7`, use:

1. `npx ctx7@latest library <name> "<specific question>"`
2. `npx ctx7@latest docs <libraryId> "<specific question>"`

Do not use external documentation lookup for general programming concepts or project-local
business logic.

### 4. Implement with focused tests

Use TDD and red-green cycles where feasible:

- RED: reproduce the problem with a failing test, or identify an existing failing test.
- GREEN: implement the smallest coherent change that satisfies the ticket.
- REFACTOR: clean up only after the targeted behavior is green.
- Test at the agreed seam: the public boundary, contract, module interface, or workflow
  that the ticket and repo conventions expect.
- Keep tests at public boundaries where possible.
- Avoid implementation-detail assertions unless the project already uses them for this
  layer.

If the ticket is too small for a new test, state why in the final response.

### 5. Verify

Run the smallest relevant feedback loops during the work, then broader checks before
finishing:

- Targeted tests for the changed behavior.
- Broader test suite if the change touches shared behavior.
- Build, typecheck, lint, or format commands expected by the repo.

If a command cannot run because of missing services, dependencies, credentials, or sandbox
restrictions, record the blocker clearly.

### 6. Review before declaring done

Run or request `code-review` against the diff before declaring the ticket done. Review
both repo standards and spec/ticket compliance. Address blocking findings, or record why
they remain unresolved.

### 7. Update the ticket record

If the ticket came from a local Markdown file:

- Move it to `done/` only when acceptance criteria are met and verification has run, or
  when the blocker is explicitly acceptable.
- If incomplete, append a short progress note with completed work, verification status,
  and remaining blockers.

If the ticket came from a tracker and tracker tools are available, update the tracker only
if the user asked you to. Otherwise, summarize what should be posted.

### 8. Commit when appropriate

Commit only when the user explicitly requested commits or the repo workflow clearly
allows commits. Do not commit just because the ticket is complete.

When committing, include:

- What changed.
- Key decisions.
- Tests or verification run.
- Remaining blockers, if any.

Do not include unrelated untracked files.

## Final Response

Report:

- What was implemented.
- Files changed.
- Verification run and results.
- Ticket update or remaining blocker.

Keep the response concise. Do not paste large diffs.

