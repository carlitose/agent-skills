# Pre-QA candidate coherence

Load before starting a run from a target branch, accepting quality evidence, or recovering a
`pre-qa-coherence-v1` block.

## New-run target

`run --base <branch>` treats `--base` as a branch name (`main` by default), not an arbitrary
revision. Before ticket snapshot selection or worktree creation, the runner force-fetches exactly:

```text
+refs/heads/<branch>:refs/remotes/origin/<branch>
```

The ledger persists `candidate-target-v1`: branch, remote, remote-tracking ref, fetched commit and
tree, canonical repository root and Git common directory, provider, and normalized remote. The
ticket snapshot, ledger base, and isolated worktree must come from that fetched commit. The fetch
does not move the caller's local branch. An invalid branch, missing remote target, non-commit, or
identity failure creates no run ledger or worktree.

## Quality boundary

Before recording a review, QA-plan, QA-execute, or verification leaf/checkpoint/stage mutation, the
runner observes the target again and validates `pre-qa-coherence-v1` against the ledger-owned
worktree. A pass requires all of the following:

- repository, normalized remote, Git common directory, and registered worktree identities match;
- the effective target follows the existing scheduler's stackability rules and recorded reconciliation;
- its freshly fetched tree equals `CandidateRef.base_tree_oid`;
- `git write-tree` equals `CandidateRef.candidate_tree_oid`;
- either `HEAD^{tree}` equals the candidate base, or HEAD and branch exactly match a recorded
  delivery/reconciliation commit whose semantic base SHA/tree is verified in Git.

The initial run target remains immutable provenance. Stacked children use the eligible parent's
published branch; integrated dependencies and reconciliations use the root target. A committed HEAD
exception is bound to the exact ledger records by digest, not inferred from commit messages or
ancestry. Ancestry is only an additional topology check. No guard operation rebases or moves HEAD.

The receipt is bound to run, ticket, artifact generation, and CandidateRef. An identical receipt is
idempotent. The runner reads the receipt back from disk before accepting evidence. Every later
quality mutation re-observes the target, so semantic target drift after a pass replaces that pass
with a blocked receipt. A different generation cannot reuse the old receipt.

## Failure and recovery

Status exposes the persisted target and the ticket's latest receipt. Typed reasons are:

- `repository-identity-mismatch`
- `worktree-identity-mismatch`
- `target-fetch-failed`
- `candidate-base-drift`
- `candidate-index-drift`
- `target-advanced-before-qa`
- `coherence-receipt-malformed`

A block records no leaf result or stage pass and grants no authority. Do not rewrite the ledger,
move local branches, rebase uncommitted bytes automatically, or reuse old QA. Preserve the receipt,
then create a fresh candidate/run from the fetched target through normal scheduling and quality.
Existing ledgers may make one persisted legacy adoption only when the remote explicitly advertises
an unambiguous symbolic default branch, there is no contradictory stacked/published lineage, and
repository, HEAD/base, candidate index, and fresh target agree. No guessed `main` or historical
rewrite is allowed. Unknown observations are null, never fabricated OIDs or cached target passes.
