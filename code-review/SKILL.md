---
name: code-review
description: "Review a diff against a fixed point along two axes: repo standards and spec/ticket compliance. Use when the user asks for review, wants changes checked before declaring done, or needs a concise actionable assessment of local changes, a branch diff, a commit, a pasted diff, or work tied to a spec or ticket."
---

# Code Review

Review a diff against a fixed point. Do not edit files, save reports, commit, or post
elsewhere unless the user explicitly asks.

The review has two independent axes:

1. **Standards**: repo conventions plus a high-signal code-smell baseline.
2. **Spec/ticket compliance**: whether the diff faithfully implements the originating
   spec, ticket, issue, PRD, or user request.

If the host can run reviewer agents, run one reviewer per axis and merge the findings.
If not, run the same two passes serially. Keep the axes separate so standards concerns
do not hide spec gaps, and spec gaps do not get mislabeled as style problems.

## Inputs

Accept:

- Local uncommitted changes.
- Staged changes.
- A branch, commit, tag, or range.
- Pasted diff text.
- A spec path under `docs/specs/`.
- A ticket path under `docs/tickets/`.
- Conversation context that names the intended change.

Ask one concise question only if both the diff and the intended fixed point are
ambiguous.

## Process

### 1. Establish the fixed point

Prefer the user's explicit base, target, or range. Record it once and do not change it
mid-review.

- For local worktree changes, review `git diff HEAD` plus staged changes if present.
- For "review commit <sha>", review that commit against its first parent.
- For "review since <branch|tag|sha>", confirm the fixed point resolves when possible
  and review `git diff <fixed-point>...HEAD` so the comparison is against the
  merge-base. Also note `git log <fixed-point>..HEAD --oneline`.
- For a branch with no explicit base, use the merge-base with the default branch when
  available.
- For pasted diffs, treat the pasted content as the fixed input.

If the chosen diff is empty, stop and say that no reviewable changes were found for the
fixed point.

### 2. Gather only relevant context

Read:

- The diff, changed files, and nearby tests.
- Public interfaces touched by the diff.
- Repo conventions from README, contributing docs, package scripts, test config,
  formatter config, architecture docs, or local docs when relevant.
- The originating spec, ticket, issue, PRD, or user request.

Resolve the spec/ticket source in this order:

1. An explicit file path, issue link, ticket link, or pasted acceptance criteria.
2. Local `docs/tickets/` or `docs/specs/` entries named by the branch, commits, or
   conversation.
3. Issue or tracker references found in branch names or commit messages, if the host can
   access them without extra setup.
4. Visible intent from the diff and conversation.

Keep context gathering proportional. Review the change, not the entire repo.

### 3. Standards axis

Check whether the diff respects local conventions and avoids high-signal maintainability
regressions.

Documented repo standards override the smell baseline. Treat smells as judgment prompts,
not automatic violations, and skip issues already caught by formatter, lint, or type
tools unless the tool output is part of the requested review.

Use this compact smell baseline:

- Mysterious name: a function, variable, type, or file name hides what it does or holds.
- Duplicated code: the same logic shape appears in more than one place in the change.
- Feature envy: code reaches into another object, module, or layer to do that layer's job.
- Data clumps: the same group of values travels together without a named concept.
- Primitive obsession: raw strings, numbers, booleans, or maps stand in for a domain idea.
- Repeated switches: the same conditional split appears across multiple locations.
- Shotgun surgery: one small behavior change requires edits in many unrelated places.
- Divergent change: one module is being changed for multiple unrelated reasons.
- Speculative generality: abstraction, hooks, parameters, or extension points serve no
  current requirement.
- Message chains: callers navigate through long object or module chains they should not
  know about.
- Middle man: a wrapper forwards work without adding a useful boundary.
- Refused bequest: a subtype, implementation, or adapter inherits or promises behavior
  it cannot honestly support.

Also look for correctness risks, missing tests around changed behavior, unsafe error
handling, dependency-direction surprises, and changes that make future work harder.

### 4. Spec/ticket compliance axis

Compare the diff to the originating spec, ticket, issue, PRD, or user request:

- Acceptance criteria satisfied.
- Non-goals respected.
- Required behavior present at the right public boundary.
- No unrelated behavior changes.
- Expected tests or verification added.
- Edge cases from the spec or ticket handled.
- User-visible behavior, API contracts, migrations, and documentation aligned with the
  requested outcome.

If no spec or ticket is available, state that this axis is limited to the user request
and visible intent from the diff.

### 5. Output

Keep the review concise and actionable. Lead with findings. Use this shape:

```markdown
## Standards

- [blocker|should-fix|nit] path:line - Problem. Suggested fix.
- No findings.

## Spec/Ticket Compliance

- [blocker|should-fix|nit] path:line - Problem. Suggested fix.
- No findings.

## Verdict

Pass | Needs changes | Blocked by missing context

## Notes

- Fixed point reviewed: <base/range/input>.
- Checks run or skipped: <commands and results, if any>.
- Open questions: <only if needed>.
```

Use `blocker` for correctness, data loss, security, broken acceptance criteria, or clear
architecture regressions. Use `should-fix` for maintainability or coverage problems that
should be addressed before declaring done. Use `nit` sparingly.

If you find no problems, say so explicitly and mention any residual risk or checks that
were not run.