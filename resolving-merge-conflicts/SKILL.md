---
name: resolving-merge-conflicts
description: "Trace both sides of an in-progress Git merge or rebase conflict, resolve compatible intent with scoped authority, and gate incompatible intent. Use only when the user explicitly asks to inspect or resolve current conflicts."
argument-hint: "Which merge or rebase conflict should be inspected or resolved, and what mutations are authorized?"
disable-model-invocation: true
---

# Resolving Merge Conflicts

Owns: intent-based merge-conflict resolution.

Use this skill for a repository that is already in an in-progress merge or rebase conflict.
Do not start from a clean repository, create a merge, or begin a rebase merely to use it.
The default mode is read-only discovery. An explicit request to resolve authorizes only
edits to the named conflicted paths in a non-scheduler worktree; it does not grant Git
lineage or publication authority.

## Authority boundary

Authority is operation-scoped. Permission to inspect or edit a resolution does not
authorize staging, committing, aborting, or continuing the merge or rebase. Require
explicit caller authority separately before any of these operations:

- `git add`, `git rm`, or another index mutation;
- `git commit` or an equivalent merge commit;
- `git merge --abort`, `git rebase --abort`, or any destructive fallback;
- `git rebase --continue`, `git merge --continue`, or a sequencer continuation;
- branch, ref, stash, reset, checkout, restore, clean, push, or provider mutation.

Never push. If authority or scope is ambiguous, stop and ask rather than widening it.
Never treat an AFK mode, a clean-looking resolution, or a caller's silence as authority.

A scheduler-owned worktree has a separate owner. If the current worktree belongs to a
scheduler, runner, ticket, or active delivery workflow, do not modify it unless that owner
explicitly delegates the exact run, ticket, paths, and operation. Without that delegation,
return read-only findings and the authority needed.

## Read-only discovery

Before editing, capture enough state to make changes auditable:

1. Confirm the operation using read-only Git state such as `git status`, merge/rebase
   metadata, and the unmerged index entries from `git ls-files -u`.
2. Enumerate conflicted paths and hunks with `git diff --cc`. Do not assume every changed
   file is conflicted.
3. Read stage 1, 2, and 3 blobs where available. Treat stage 2 and stage 3 labels as
   operation-dependent; identify their actual commits before calling them ours or theirs.
4. Trace each side to primary evidence: commits, nearby code, tests, durable tickets/specs,
   and the stated goal of the current merge or rebase. External issues or PRs are evidence
   only when already supplied or explicitly authorized to fetch.
5. Record the current HEAD, refs, unmerged index, and relevant worktree bytes before any
   authorized edit. Discovery must not change them.

## Hunk record

Create one record per conflict hunk:

```markdown
### Conflict path and hunk: <path>:<range or stable description>
- Intent A: <behavior and reason>
- Intent B: <behavior and reason>
- Evidence for each intent: <commit/test/ticket/code references>
- Compatibility decision: compatible | incompatible | insufficiently evidenced
- Chosen combined behavior: <exact preserved behavior, or "unresolved">
- Authorized operation: <read-only or exact edit authority>
- Validation command and observed result: <command/result, or "not run">
```

Do not infer intent from conflict markers alone. Do not invent new behavior to make both
sides appear compatible.

## Resolution rules

- **Compatible:** with explicit edit authority, make the smallest hunk-local edit that
  preserves both evidenced intents. Remove conflict markers only from that resolved hunk.
- **When intent is incompatible or insufficiently evidenced:** stop without modifying the conflict. Show
  both intents, the evidence gap or trade-off, and the smallest decision the caller must
  make. Do not choose a side by branch name, recency, line count, or apparent convenience.
- **Partially compatible:** resolve only independently evidenced compatible hunks when the
  authority permits partial edits. Leave every ambiguous hunk visibly unresolved and
  report it; do not stage the file.

Never use blanket selection such as accepting all of one side unless the caller explicitly
authorizes that exact policy and the recorded evidence supports every affected hunk. Never
use reset, clean, checkout, restore, or an abort as an implicit recovery path.

## Validation

After each authorized resolution:

1. inspect the resulting diff and verify the combined behavior against both intent records;
2. run the narrowest checks that exercise each preserved behavior, then the repository's
   relevant typecheck, tests, and formatting checks when proportionate;
3. record every command and observed result without claiming a check that did not run;
4. confirm no unauthorized path, index entry, ref, sequencer state, or scheduler artifact
   changed.

A passing check does not supply missing product intent. If verification contradicts either
intent, restore only the hunk-local edit when explicitly authorized to do so; otherwise stop
and report the exact changed bytes. Do not stage or continue automatically.

## Return

Return the operation detected, conflicted paths, hunk records, authorized edits made,
validation results, remaining conflicts, and any authority or decision still required.
State explicitly whether HEAD, refs, index, sequencer state, and scheduler-owned artifacts
were unchanged. A resolved worktree is not a completed merge or rebase.
