# Necessary actions and closure hygiene

Applies in every delivery lane. This is an agent procedure, not a shell interceptor,
scheduler or automatic deletion hook. Source: [approved Q1–Q4](../docs/specs/local-actions-and-closure-hygiene.md).

## Necessary actions
Within the user's task, perform necessary actions that are local and reversible without
asking again: test builds/installations on a connected phone or emulator, development
dependencies, a development server, branches and commits. Opening PRs in the user's
repository is also covered: this explicit remote exception covers open PRs, not issue
publication or messages to others. A necessary step is not by itself authority for any
external or destructive effect. Respect an explicit restriction or actual runtime refusal;
never bypass it. Preserve personal device data and do not expose a server publicly by inference.

Merge, store or production publication, spending, credentials and accounts, deletion of
other people's data, and messages to others still need their own explicit authority.
This grants no Pi synchronization or reload. Report actions taken and remaining gates;
ask only for a genuinely missing decision, not a second confirmation of the task.

## Closure
When a PR is merged or closed, or the session ends, inventory Git worktrees, local branches,
agent temporaries and agent-created work directories inside Git common state. An open PR
or active handoff keeps the resources needed to resume. Ending one session does not end
another task or a runner. For existing clutter from earlier work, present a folder-by-folder
proposal before deletion; do not treat a disk inventory as permission.

1. **Prove ownership and disuse.** Identify exact paths attributable to the agent's work;
   check Git registration, retained heads, dirty/ignored/untracked files, active references,
   locks and interrupted Git operations. Names, age and `[gone]` are not proof. Protect
   ambiguous or other agents' resources and the invocation checkout until safely left.
2. **Prove recoverability.** For work absent from `main` and the remote, save a binary patch
   against an identified base commit, copies of untracked files, and a Git bundle for unique
   commits as needed, outside the removal target. An empty patch does not retain unique
   commits; a diff does not retain untracked files. Verify recovery before deleting the
   source. Preserve file modes and any nonregenerable ignored files. If uncertain, keep it
   and name the missing proof; never copy secrets into a public artifact.
3. **Remove only eligible resources.** Remove unused, recoverable agent worktrees, local
   branches whose remote no longer exists, temporaries and agent work directories. Retain
   user data, `.git/private`, and `node_modules`/`.venv` in the primary checkout. Do not
   traverse symlinks or junctions. No force removal, broad recursive wipe, hard reset, or
   `git clean -fdx`. Use ordinary `git worktree remove`; if it refuses, retain and report.
   For a runner worktree, its refusal must not be bypassed: use its existing
   [ownership, GC and receipt procedure](../ticket-autopilot/references/worktrees.md)
   only in an authorized Autopilot lane. In skills-only, preserve runner-owned resources
   and report the required owner action rather than starting the runner. A recovery copy
   does not close a runner gate. Do not delete remote branches or change lifecycle state.
4. **Read back.** Confirm removals and Git registration, then delete only eligible local
   branches. Fast-forward the main checkout only when safe; preserve unrelated changes,
   never reset or switch somebody else's checkout. Report removed/protected resources,
   recovery paths, before/after sizes and unresolved cleanup. Stop only development
   processes owned by this task and no longer needed.

Completion criterion: every inventoried task-owned resource is removed with recovery proof,
retained for a named use/protection, or handed off with a recovery path; no unique work is lost.

## Disk alarm
Resolve the real Git common directory with `git rev-parse --git-common-dir`: a worktree's
`.git` may be a file. Measure file sizes without following links or reading private contents.
Above 1 GB (1,000,000,000 bytes), report the five largest immediate subdirectories, ranked
by bytes without overlapping subtrees, and apply only eligible closure/run cleanup. The
threshold is not extra deletion authority. Do not inspect `.git/private` contents to explain
its size. Show before/after totals; an unreadable subtree makes a measurement partial,
not zero. If fewer than five directories exist, report all; identify any large direct files.

## Integrated-run material
Only when every ticket is durably integrated, no live operational reference requires the
material, and the observed integration timestamp is more than 14 days old (not mtime or a
folder name), remove regenerable heavy copies: source archives/bundles, copied environments,
Python virtualenvs and `node_modules`. Unknown integration time means keep, not expired.

Keep the ledger, history, manifests, receipts and unique evidence. Fourteen days is a minimum
age for pruning heavy copies, not an expiry for records. Classify by contents and dependencies,
not filename extension: a bundle holding unique commits stays. Keep a referenced archive if
its loss breaks verification, replay or recovery and it cannot be exactly regenerated from
retained inputs. Preserve active, recent, nonintegrated, locked or ambiguous runs. Do not
rewrite historical evidence hashes or label absent artifacts as validated.

Completion criterion: removed heavy material is reproducible independently of the removed
copy, retained records remain usable, and each skipped run/artifact has a stated reason.
