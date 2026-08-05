# Ticket Autopilot Autonomous Stacked Delivery

## Type

Architecture decision

## Status

Planning baseline

## Sources

- [GitHub issue #23 — Possibility to give autopilot authority to merge without asking](https://github.com/carlitose/agent-skills/issues/23)
- Human decision on 2026-08-05: avoid repeating code review for downstream stacked PRs
  when merging their parent changes only commit lineage.
- [Candidate invalidation decision](./candidate-invalidation-decision.md)

## Goals

- Add an explicit, run-scoped autonomous merge policy while keeping manual merge as the
  default.
- Merge each eligible PR without a new human prompt only after fresh provider checks and
  an atomic expected-head guard.
- Reconcile a stacked child after its parent merges without repeating review, QA, or
  verification when the semantic base, candidate content, and ticket contract are exactly
  unchanged.
- Invalidate all semantic evidence when any of those semantic inputs changes.

## Non-Goals

- Inferring merge authority from `AFK`, repository access, or silence.
- Bypassing branch protection, required checks, review policy, or merge queues with an
  administrator override.
- Reusing evidence across different tree identities through path-based or heuristic impact
  analysis.
- Treating a changed child tree or changed base tree as harmless because filenames appear
  unrelated.

## Current Behavior and Root Cause

- The public contract forbids auto-merge and requires a separate authorization bound to
  each observed PR head SHA.
- The delivery implementation already models GitHub's expected-head merge capability with
  `gh pr merge --match-head-commit`, while ticket `02` owns making that guarded mutation
  immediate and replay-safe.
- `CandidateRef` v1 contains `base_sha`, `tree_oid`, and `ticket_digest`. Stack
  reconciliation rebases the child, constructs a new ref from the rebased HEAD, and always
  calls `prepare_reconciliation`, which clears semantic leaf artifacts and restarts at
  `review`.
- A fast-forward, squash, or merge-commit parent integration can change commit SHA while
  preserving both the parent's tree and the child's resulting tree. Commit lineage changed;
  the reviewed code did not.

## Decision

### Separate semantic identity from delivery lineage

Content-bound evidence uses a versioned semantic candidate identity:

```json
{
  "base_tree_oid": "<tree of the PR base used for the ticket diff>",
  "candidate_tree_oid": "<tree delivered by the ticket branch>",
  "ticket_digest": "<normalized envelope and acceptance digest>",
  "contract_version": 2
}
```

Delivery lineage is stored separately and includes provider, PR ID, base branch, base SHA,
and current head SHA. Review, QA, and verification bind to the semantic candidate; provider
mutation and merge authorization bind to delivery lineage.

This narrows the earlier D6 decision without introducing selective reuse: any semantic
candidate change still invalidates all semantic artifacts. A lineage-only SHA change is no
longer classified as a candidate-content change.

### Content-equivalent stack reconciliation

After live readback proves the parent integrated, reconciliation must:

1. verify the recorded child remote head and rebase with the existing force-with-lease
   guard;
2. resolve the new target base tree and rebased child tree from Git, not caller claims;
3. recompute the semantic candidate using those two tree OIDs and the exact ticket digest;
4. preserve the existing review, QA, verification, and cache artifacts only when the new
   semantic candidate equals the old one exactly;
5. otherwise clear every semantic artifact and restart normal review;
6. always update delivery lineage, retarget/read back the PR, and require checks for the new
   head before merge.

The ledger records an equivalence or invalidation receipt with old/new semantic identities,
old/new heads, base identity, and artifact generation. Equality is exact and deterministic;
there is no agent-authored “non-semantic change” assertion.

### Explicit autonomous merge grant

`run` gains a policy equivalent to:

```text
--merge-policy manual|autonomous
--merge-actor <identity>
--merge-evidence <durable reference>
```

`manual` remains the default. `autonomous` requires actor and evidence at run creation and
records a grant bound to repository identity, run ID, normalized ticket-set digest, provider,
and policy version. It authorizes the runner to request merges for eligible tickets in that
run; it is not itself a claim that any particular head is safe.

For every merge, the runner still must:

- hold the run lock and observe the exact open PR and current head live;
- confirm the semantic candidate remains fully validated;
- confirm required provider checks/policies and non-bypassed merge eligibility;
- invoke only the provider's expected-head operation for the just-observed head;
- read the result back and persist idempotent receipts before marking `integrated`.

GitHub documents `--match-head-commit` as the stale-head guard. The runner must not use
`--admin`. It must not delegate to provider auto-merge unless the provider contract proves
that the queued/automatic request remains pinned to the exact head; otherwise it waits and
performs the guarded merge when requirements are green. Providers without atomic
expected-head capability remain gated.

The autonomous grant survives a lineage-only stack reconciliation, but the actual merge
attempt is always rebound to the freshly observed new head. A semantic candidate change
requires full revalidation before the grant can be used again.

## Semantic Invariants

- Equal semantic candidates mean equal base tree, candidate tree, ticket contract, and
  candidate contract version.
- A changed base tree, candidate tree, ticket digest, or contract version reruns complete
  semantic validation.
- A new PR head never inherits a one-shot manual head authorization.
- A standing autonomous grant cannot bypass current-head observation or provider policy.
- Simulated provider evidence cannot authorize a live merge.
- Crash recovery never sends a second merge before reconciling the provider state.

## External Contract and Compatibility

- Add the explicit merge-policy arguments and expose grant identity/status in plan, status,
  and final reports.
- Split semantic candidate and delivery lineage in leaf, cache, verification, ledger, and
  report contracts.
- Version incompatible persisted state explicitly. Active older ledgers are rejected with
  an actionable error or migrated only by a separately validated explicit command; they are
  never silently treated as semantic-candidate v2.
- Update `ticket-autopilot/SKILL.md` so `AFK` and autonomous merge authority remain distinct.

## Failure Modes

- Parent merge resolution or unrelated base advancement changes the base tree.
- Rebase conflict, dropped commit, generated-file drift, or changed child tree.
- Remote child head changes before force-with-lease push.
- Required checks are pending or fail on the rebased head.
- Provider merge queue semantics cannot prove exact-head pinning.
- Crash occurs before merge, after provider mutation, or before ledger persistence.
- A resumed run presents a different grant, ticket-set digest, or repository identity.

All cases gate, revalidate, or reconcile from live state; none becomes an optimistic pass.

## Alternatives

- Keep `base_sha` in semantic identity: safe but causes the redundant reviews reported by
  the user.
- Ignore only `base_sha` during equality: rejected because a different base tree can change
  the reviewed diff and runtime content.
- Preserve only code-review output while rerunning QA and verification: rejected because it
  creates inconsistent identity rules for artifacts with the same exact semantic inputs.
- Enable GitHub `--auto` blindly: rejected because a later head change must not inherit an
  unproven merge request.
- Make autonomous merge the default: rejected because merge authority must be explicit.

## Implementation Slices

1. Ticket `05` introduces semantic candidate v2, separate delivery lineage, exact
   content-equivalent stack reconciliation, and fail-closed evidence preservation.
2. Ticket `06` adds the explicit run-scoped autonomous grant and drives the existing
   expected-head merge critical path without per-PR prompts.
3. Ticket `07` documents the final public workflow after both slices and ignored-source
   support are complete.

## Verification Strategy

- Unit tests for semantic identity equality, ledger validation, grant scope, and stale-head
  rejection.
- Git integration fixtures for fast-forward, squash-equivalent, merge-commit-equivalent,
  changed-base-tree, changed-child-tree, conflict, and remote divergence cases.
- Stateful provider tests for pending/failed checks, exact-head merge, head changes, merge
  queue gates, crash windows, and idempotent recovery.
- A three-ticket stack proving each downstream ticket keeps prior semantic review evidence
  across lineage-only parent merges and reruns it after any planted semantic drift.
- Live provider behavior remains an explicit evidence gate until observed with disposable
  credentials.
