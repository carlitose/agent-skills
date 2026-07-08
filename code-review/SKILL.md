---
name: code-review
description: Review a diff against a fixed point along two axes: repo standards and spec/ticket compliance. Use when the user asks for review, wants changes checked before declaring done, or needs a concise actionable assessment of local changes, a branch diff, a commit, a pasted diff, or work tied to a spec or ticket.
---

# Code Review

Review a diff against a fixed point. Do not edit files, save reports, commit, or post
elsewhere unless the user explicitly asks.

The review has two independent axes:

1. **Standards**: repo conventions plus high-signal code smells.
2. **Spec/ticket compliance**: whether the diff faithfully implements the originating
   spec, ticket, or user request.

If the host can run reviewer agents, run one reviewer per axis and merge the findings.
If not, run the same two passes serially.

## Inputs

Accept:

- Local uncommitted changes.
- Staged changes.
- A branch, commit, or range.
- Pasted diff text.
- A spec path under `docs/specs/`.
- A ticket path under `docs/tickets/`.
- Conversation context that names the intended change.

Ask one concise question only if both the diff and the intended fixed point are
ambiguous.

## Process

### 1. Establish the fixed point

Prefer the user's explicit base or target. Otherwise:

- For local changes, review `git diff HEAD` plus staged changes if present.
- For a named commit, review that commit against its first parent.
- For a branch, use the merge-base with the default branch when available.
- For pasted diffs, treat the pasted content as the fixed input.

Record the fixed point in the output. Do not change it mid-review.

### 2. Gather only relevant context

Read:

- The diff and changed files.
- Nearby tests and public interfaces touched by the diff.
- Repo conventions from README, package scripts, test config, formatter config, or local
  docs when relevant.
- The originating spec or ticket, if supplied or obvious from file paths.

Keep context gathering proportional. Review the change, not the entire repo.

### 3. Standards axis

Check whether the diff respects local conventions and avoids high-signal maintainability
regressions.

Use this compact smell baseline:

- Mysterious names.
- Duplicated code.
- Feature envy.
- Data clumps.
- Primitive obsession.
- Repeated switches.
- Shotgun surgery.
- Divergent change.
- Speculative generality.
- Message chains.
- Middle man.

Also look for correctness risks, missing tests around changed behavior, unsafe error
handling, dependency-direction surprises, and changes that make future work harder.

### 4. Spec/ticket compliance axis

Compare the diff to the originating spec, ticket, or user request:

- Acceptance criteria satisfied.
- Non-goals respected.
- Required behavior present at the right public boundary.
- No unrelated behavior changes.
- Expected tests or verification added.
- Edge cases from the spec or ticket handled.

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