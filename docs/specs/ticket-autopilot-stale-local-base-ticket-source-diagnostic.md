# Ticket-Autopilot Stale Local Base Ticket Source

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-stale-local-base-ticket-source-diagnostic`
- Role: `spec`
- Standalone: true

### Children

- [SB-01 resolve a fast-forward upstream before ticket-source classification](../tickets/ticket-autopilot-stale-local-base-ticket-source/01-resolve-fast-forward-upstream-base.md)

## Type

Diagnostic spec

## Status

Diagnosed; ready for ticket execution.

## Diagnosis Report - lens: source-ref resolution

### Root cause

`ticket-autopilot plan` and `run` pass the selected `--base` directly to
`ticket_source._classify()`. That function resolves the symbolic ref once and classifies
every ticket path only against the resulting local commit. It does not examine the local
branch's configured upstream, even when the already-fetched upstream is a strict
fast-forward descendant.

After the runner integrates a PR remotely it intentionally leaves the user's local `main`
branch unchanged. A following ticket batch can therefore be committed on the integrated
remote base while local `main` still points to its parent. `_classify()` sees no ticket blobs
at local `main` and emits `ticket input is untracked and not ignored`, although the same
paths are tracked and exact at `refs/remotes/origin/main`. The rejection describes the stale
selected commit, not the ticket source's real integration state.

### Evidence

- In the reproduced repository, local `main` is
  `3f0946a27fdbc45eb78f4f5e75b94b099dd4b766` and the fetched
  `refs/remotes/origin/main` is
  `50e6ab9d94f5c3bd6baa1124e8177ad6898734ed`.
- `git merge-base --is-ancestor main refs/remotes/origin/main` passes, proving a safe
  fast-forward relationship rather than divergence.
- On the exact integrated CB-01 ticket folder,
  `inspect_ticket_source(..., base_ref="main")` raises the false untracked error.
- The same call with `base_ref="refs/remotes/origin/main"` returns `tracked` and selects
  `50e6ab9d94f5c3bd6baa1124e8177ad6898734ed`.
- The public `plan` command reproduces the same fail/pass pair. No ticket content or ignore
  rule changes between the two invocations.
- Existing integration tests deliberately assert that provider integration does not advance
  local `main`; that safety property makes source-base resolution, not local-branch mutation,
  the correct fix location.

### Feedback loop built

The deterministic regression needs a repository with a local base branch, a configured
remote-tracking upstream that is one commit ahead, and a ticket folder present only in that
upstream commit while remaining available in the current checkout. Before the fix,
classification against the local branch must fail with the false untracked error; explicit
classification against the upstream must pass.

The green test must invoke both `plan` and `run` with the local branch name and prove they
select the upstream SHA without moving the local branch. A control must keep genuinely
unintegrated, non-ignored tickets rejected.

### Fix location and approach

Add a narrow selected-base resolver in `ticket_source.py`. When `--base` denotes a local
branch with a configured, locally available upstream and the local commit is an ancestor of
that upstream, classify and snapshot against the upstream commit. Do not fetch, update the
local branch, or mutate the checkout. Preserve the explicit local commit when it is equal to
or ahead of its upstream; fail closed on divergence instead of guessing which history is the
delivery target. Full commit and remote-tracking refs remain literal.

Persist the resolved commit in `selected_base_sha`, so `run` creates its isolated worktree
from the same commit that made ticket-source classification pass. Cover tracked and ignored
source modes because both must start from the resolved delivery base.

### Alternatives ruled out

- **Fast-forward local `main` after every merge.** Rejected: existing behavior intentionally
  avoids mutating user branches, and another worktree may have `main` checked out.
- **Tell operators to pass `origin/main`.** Rejected as the only remedy: it leaks a recurring
  recovery detail into AFK operation and leaves the default symbolic-base path inconsistent.
- **Fetch inside `plan`.** Rejected for this ticket: `plan` is read-only/provider-neutral and
  the observed defect already reproduces with a current remote-tracking ref. Network refresh
  policy is a separate concern.
- **Accept any working-tree ticket absent from the selected base.** Rejected: that would
  weaken the tracked-or-ignored source invariant and admit genuinely unintegrated input.
- **Prefer upstream across divergence.** Rejected: ancestry no longer proves that upstream is
  a safe continuation of the selected local base.

### Confidence: high

The fail/pass pair changes only the resolved base ref, the ancestry is proven, and the
responsible function is the sole classifier and snapshot source for both `plan` and `run`.
