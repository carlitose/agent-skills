# Repository-wide autonomous merge-all authority

## Artifact Graph

- Artifact ID: `spec:ticket-autopilot-repository-wide-merge-all`
- Role: spec
- Standalone: true

### Children

- [RMA-01 — Add repository-wide autonomous merge-all authority](../tickets/ticket-autopilot-repository-wide-merge-all/01-add-repository-wide-autonomous-merge-all-authority.md)

## Type

Feature specification.

## Decision

Ticket Autopilot will support one explicit, durable, repository-wide autonomous merge
authority that applies across all current and future runs bound to that exact repository.
Once granted, the operator can use `merge-all` without creating a separate autonomous grant
for every run or approving every eligible PR head.

The repository-wide grant replaces repetitive **merge authorization only**. Every merge
still uses the existing fresh live provider eligibility, exact-head mutation, queue/direct
mode, provider readback, and integration reconciliation contracts. It does not approve
content conflicts, finalization-environment gates, source publication, repository
bootstrap, wiki sync, Pi synchronization, cleanup, or any other non-merge authority.

## Current behavior

Autonomous merge grants are run-scoped. A run may receive one during creation or later via
`grant-autonomous-merge`, but another run needs another explicit grant even when both runs
belong to the same repository and operator decision.

This preserves authority correctly but makes “merge every eligible Ticket Autopilot PR in
this repository” repetitive. The existing exact-head safety path already separates durable
standing authority from the volatile PR head; the missing contract is a higher-level,
repository-bound authority source plus deterministic cross-run scheduling.

## Goals

- Record merge authority once for one exact repository and provider.
- Reuse it across current and future non-terminal runs in that repository.
- Provide one `merge-all` command that finds and processes every currently merge-ready run
  under one repository lock.
- Preserve the existing expected-head, checks, approvals, rules, mergeability, queue, and
  live readback requirements for every PR independently.
- Keep non-merge gates visible without repeatedly asking about otherwise eligible PRs.
- Support explicit revocation before any later provider mutation.

## Non-goals

- Machine-wide authority across unrelated repositories.
- Inferring authority from AFK mode, access, credentials, silence, or natural-language
  fragments inside the runner.
- Approving content conflict choices or any non-merge gate.
- Creating Git repositories, configuring `origin`, publishing initial bases, or changing
  repository visibility; the zero-repository bootstrap spec owns those operations.
- Merging a stale, unverified, simulated, pending, failed, unknown, or queue-uncertain head.
- Bypassing branch rules, approvals, required checks, provider capabilities, or exact-head
  compare-and-swap behavior.
- Rewriting existing run grants or historical authority events.

## Authority model

### Repository grant

Add an explicit command:

```text
ticket-autopilot grant-repository-autonomous-merge \
  --repo <absolute-repository> \
  --scope current-and-future-runs \
  --actor <identity> \
  --evidence <durable-ref>
```

The immutable grant binds:

- canonical repository identity and Git common directory;
- provider and normalized remote repository identity;
- scope `current-and-future-runs`;
- actor and durable evidence;
- grant ID, schema version, creation sequence, and content digest.

State lives under the repository Git common directory, outside any one run ledger, behind a
repository-authority lock. Persist intent before any run adoption or provider observation.
Exact replay is idempotent; contradictory identity, actor, evidence, provider, scope, or
digest fails closed.

The user request to build this feature is not itself a live repository grant. An operator
must invoke the command with explicit actor/evidence after the capability is integrated.

### Run adoption

Before an autonomous merge eligibility check, a manual run may adopt the active repository
grant. Adoption appends an immutable run event containing the grant ID/digest and repository
identity. It changes only merge policy. It must not consume a gate or copy the grant into a
form that survives repository-grant revocation unchecked.

Before every provider mutation, the runner re-reads the repository authority under the same
repository lock and proves that the adopted grant remains active and exact. Run-local
autonomous grants continue to work unchanged and do not become repository grants.

### Revocation

Add:

```text
ticket-autopilot revoke-repository-autonomous-merge \
  --repo <absolute-repository> \
  --actor <identity> \
  --evidence <durable-ref>
```

Revocation appends an immutable event and prevents every not-yet-started or not-yet-mutated
merge attempt from using the grant. It never rewrites run history or undoes an integrated
merge. An unresolved provider mutation remains a reconciliation problem and cannot be
silently retried under changed authority.

## `merge-all` orchestration

Add:

```text
ticket-autopilot merge-all --repo <absolute-repository>
```

Under one repository authority/scheduler lock, the command:

1. validates the active repository grant;
2. discovers run ledgers only below that repository's canonical Git common state;
3. validates every ledger independently and rejects duplicate run identity or path escape;
4. selects only tickets already verified/PR-open or recoverably provider-merge-gated;
5. skips and reports implementation, review, QA, semantic conflict, finalization,
   source-mode, bootstrap, wiki, Pi-sync, pause, canceled, failed, or cleanup states;
6. serially adopts the grant where allowed;
7. executes the existing fresh exact-head merge critical path independently per PR;
8. records provider and integration readback in each owning run ledger; and
9. returns a deterministic per-run result: integrated, already-integrated, gated, skipped,
   failed-before-mutation, or reconciliation-required.

One run failure does not authorize bypass and does not prevent later independently eligible
runs from being evaluated. The command never executes implementation work or mutates a
candidate to make it mergeable.

## Semantic invariants

1. Manual remains the default when no active exact repository grant exists.
2. Repository authority is explicit, actor/evidence-bound, append-only, lock-serialized,
   and checked before every provider mutation.
3. Scope is one canonical repository and provider, not a filesystem subtree or account.
4. Current and future run adoption is auditable and cannot transfer authority elsewhere.
5. Every merge uses a fresh live PR/head/checks/rules/approvals/mergeability observation.
6. Every direct merge uses the expected head; queue mode requires proven queue support and
   intent-bound readback.
7. A changed CandidateRef, delivery lineage, PR ID, repository identity, or provider state
   invalidates volatile eligibility evidence.
8. Revocation blocks later mutation but cannot falsify or undo historical integration.
9. Non-merge gates remain separate even when they block eventual merge-all progress.
10. Repository merge authority grants no bootstrap, source, finalization, wiki, Pi,
    cleanup, issue, visibility, force-push, or conflict-resolution authority.

## Failure modes

| Failure | Required result |
|---|---|
| No active repository grant | `merge-all` fails before provider observation. |
| Grant path or envelope is corrupt/symlinked | Fail closed without adopting any run. |
| Same grant replayed exactly | Return the existing grant without duplicate history. |
| Contradictory actor/evidence/repository/provider | Reject without changing authority. |
| Run already has a contradictory local grant | Report the run as gated; never overwrite either grant. |
| Run is mid provider mutation | Preserve its merge intent and require exact reconciliation. |
| PR head changes | Re-read and merge only the newly eligible exact head. |
| Checks/policy/approval/mergeability fail | Keep that run gated and continue evaluating independent runs. |
| Non-merge gate is open | Report skipped/gated; do not approve it. |
| Revocation races with merge-all | Repository lock establishes one order; mutation must observe active authority immediately before provider call. |
| Crash between run adoption and merge | Replay revalidates repository authority and live provider state. |
| Crash after provider mutation | Existing exact external-merge reconciliation owns recovery. |

## Security and data concerns

- Repository discovery must never scan or accept ledgers outside the canonical Git common
  state.
- Authority and run ledgers use integrity envelopes, durable atomic writes, fsync where
  supported, and append-only hash-linked events.
- Evidence strings are provenance, not authentication; output must not expose secrets.
- Provider mutation remains serialized and provider receipts remain evidence-classified.
- `merge-all` output must identify every skipped/gated run so convenience cannot hide work.

## Compatibility

Existing manual and run-autonomous ledgers remain valid. A repository grant is a new
optional authority source; no existing run is silently changed merely because the code is
upgraded. Existing per-run grants retain their exact semantics.

## Implementation slice

One tracer-bullet ticket owns:

- repository-authority grant/revoke state and validation;
- run adoption without copying revocation-proof authority;
- `grant-repository-autonomous-merge`, revoke, and `merge-all` CLI commands;
- deterministic cross-run discovery, locking, result projection, and crash replay;
- reuse of the existing autonomous exact-head critical path without duplicating policy;
- status/documentation/context-budget updates; and
- disposable multi-run tests plus full regression and forward scenarios.

## Acceptance outcomes

1. One explicit repository grant authorizes merge eligibility for multiple existing runs
   and a later-created run without per-run merge prompts.
2. `merge-all` integrates every independently eligible exact head and reports non-merge
   gates without consuming them.
3. A changed head receives fresh live eligibility and expected-head mutation.
4. Exact grant replay is idempotent; contradictory authority and forged state fail closed.
5. Revocation prevents every later provider mutation, including an already-adopted run.
6. A run-local grant continues to work without repository authority.
7. No test or implementation path uses admin bypass, force push, public visibility, or
   authority transfer to bootstrap/wiki/Pi/finalization/conflict resolution.
8. Status exposes repository grant identity, active/revoked state, run adoption, merge-all
   outcomes, and remaining non-merge gates.

## Verification strategy

### Unit

- Grant/revoke envelope, exact replay, contradiction, integrity, symlink, and path tests.
- Run adoption and revocation recheck tests.
- Deterministic run discovery and classification tests.

### Integration

- Multiple disposable run ledgers and real local Git branches with a deterministic GitHub
  command boundary.
- Eligible, changed-head, check-failed, non-merge-gated, already-integrated, conflicting
  local-grant, and crash/replay cases in one merge-all invocation.
- Prove all provider mutations retain exact expected-head arguments.

### Regression

- Full Ticket Autopilot and extension tests, forward scenarios, static checks, artifact
  audit delta, and controlled context measurement.

### Live boundary

A separately invoked repository grant may exercise `merge-all` on real open PRs. Local
simulations cannot claim live provider integration, and the implementation delivery's own
merge authority remains separately scoped.
