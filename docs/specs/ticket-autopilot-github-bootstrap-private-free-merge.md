# Ticket Autopilot GitHub Bootstrap and Private-Free Merge

- Status: Accepted
- Type: Bug analysis
- Date: 2026-08-29

## Artifact Graph

- Artifact ID: `artifact:spec-ticket-autopilot-github-bootstrap-private-free-merge`
- Role: `spec`
- Standalone: true

### Children

- [GPM-01 Accept GitHub private-plan policy evidence](../tickets/ticket-autopilot-github-bootstrap-private-free-merge/done/01-accept-private-plan-policy-evidence.md) — source lifecycle completed in an aborted, non-delivered run.
- [GPM-01R Recover GitHub private-plan policy evidence delivery](../tickets/ticket-autopilot-github-bootstrap-private-free-merge/01r-recover-private-plan-policy-evidence-delivery.md)
- [GPM-02 Add audited private GitHub repository bootstrap](../tickets/ticket-autopilot-github-bootstrap-private-free-merge/02-add-audited-private-repository-bootstrap.md)

## Summary

Ticket Autopilot must not require an operator to leave the audited workflow merely to
create a new private GitHub repository, publish its first base branch, or merge into an
unprotected private repository whose account cannot use GitHub branch rules.

Two independent gaps caused the observed stop:

1. the normalized provider surface starts at pull-request delivery, so repository creation
   and first-base publication have no durable intent, replay, or readback path; and
2. GitHub's active-rules endpoint returns a plan-specific HTTP 403 for private repositories
   on plans without branch rules, but the adapter treats every non-zero response as an
   opaque provider failure.

The exact plan-limitation response proves that branch rules and merge queues are
unavailable for that repository. It is not equivalent to an arbitrary 403. The adapter may
therefore record this exact response as `feature-unavailable`, keep evaluating live PR
head, mergeability, checks, and approvals, and select direct merge. Every other rules
readback error continues to fail closed.

The incident run `pi-plan-customization-v2-20260829` has already been reconciled after an
external exact-head merge; this spec prevents recurrence rather than rewriting that run.
The first implementation attempt, `GPM-01`, later stopped before commit on a local
source-mode provenance gate and was aborted. Replacement `GPM-01R` owns fresh delivery;
no candidate-bound evidence or completion claim transfers from the aborted run.

## Observed Behavior

For `carlitose/pi-personal-config`:

- the repository did not exist, then existed privately without a default branch;
- Ticket Autopilot had no provider operation for repository creation;
- its finalizer could publish a ticket branch but would not establish the missing `main`;
- direct `gh api repos/{owner}/{repo}/rules/branches/main` and the classic branch
  protection endpoint both returned HTTP 403 with
  `Upgrade to GitHub Pro or make this repository public to enable this feature.`;
- the runner opened a `provider-merge` gate even though GitHub reported the exact PR head
  and the repository could not have an active protected-branch or merge-queue policy;
- PR #1 at head `b61df52a335a4ee882ca4f4a5bfa15ecf0c40b4d` was merged externally and the
  existing external-merge recovery path completed the run.

The installed runner copies also lagged the repository source and did not expose
`grant-autonomous-merge`. That explains an adjacent capability mismatch, but it does not
cause the rules-endpoint 403 and does not justify weakening manual merge authority.

## Expected Behavior

### Audited repository bootstrap

A dedicated Ticket Autopilot command can bootstrap a new **private** GitHub repository
from an existing local Git repository before a folder run begins.

The command requires:

- an absolute local repository path;
- an explicit `OWNER/REPOSITORY` target;
- the local base branch and exact base commit;
- a non-empty actor and durable evidence reference; and
- an explicit private visibility decision.

It persists an immutable, repository-bound intent under the local Git common state before
any remote mutation. It then creates or safely adopts only the exact private repository,
configures `origin` only when absent or already equivalent, publishes the exact base commit
without force, establishes or verifies the default branch, and records live readback.

Exact replay is idempotent. A contradictory target, visibility, remote URL, branch, SHA,
actor, or evidence fails closed. Crash recovery may finish a partially applied matching
bootstrap after live readback; it must never delete a repository, overwrite a remote
branch, change visibility, force-push, or infer merge authority.

Repository bootstrap is a prerequisite transaction, not application delivery. It grants
no PR, merge, wiki-sync, or future repository-creation authority.

### Plan-limited policy readback

The GitHub adapter parses the failed active-rules response as structured JSON. It may
classify the result as `feature-unavailable` only when all of these are true:

- HTTP status is `403`;
- the provider message exactly identifies the GitHub Pro/public-repository plan limit; and
- the documentation URL identifies GitHub's active branch rules endpoint.

The resulting live receipt contains the explicit policy-observation status and an empty
active-rules list. Check rollup, exact head, approvals, mergeability, PR state, and atomic
`--match-head-commit` behavior remain mandatory. The adapter selects direct mode because
the plan-limitation evidence excludes an active merge queue.

Authentication errors, missing scopes, rate limits, malformed bodies, generic 403s,
organization restrictions, network failures, and unknown responses remain provider gates.
A successful rules response continues to drive direct-versus-queue behavior exactly as it
does now.

## Goals

- Let an explicitly authorized agent create the exact private repository and first base
  branch without instructing the human to run `gh` or `git push`.
- Preserve append-only provenance and deterministic crash recovery around that remote
  mutation.
- Let private GitHub Free repositories use the existing guarded exact-head merge path when
  GitHub itself proves branch-rule features are unavailable.
- Keep arbitrary policy-observation failures fail-closed.
- Make responses explain whether policy was observed or unavailable by plan.

## Non-Goals

- Public or internal repository creation.
- Deleting, renaming, transferring, changing visibility, or force-pushing repositories.
- Adopting a non-empty remote base whose SHA differs from the authorized local base.
- Bypassing branch protection, merge queues, required checks, reviews, or administrator
  restrictions.
- Treating `Autorizzo tutti i merge`, AFK mode, access, silence, or repository bootstrap as
  merge authority.
- Automatically updating installed skill copies or migrating unrelated historical runs.
- Changing Azure DevOps behavior.

## Root Cause and Evidence

### Missing bootstrap ownership

`RemoteProvider.operation` exposes PR creation/readback, checks, approvals, retargeting,
and expected-head merge. `DeliveryFinalizer._ensure_push` owns only the generated ticket
branch. There is no command, capability, intent record, or provider receipt for creating a
repository or publishing its first base branch. The earlier assistant therefore chose
between an untracked direct mutation and a human prerequisite.

GitHub CLI documents `gh repo create --private --source=<path> --push`, demonstrating that
the provider supports the operation. The runner still needs a narrower staged adapter so
intent can be persisted before mutation and partial completion can be read back safely.

### Over-broad 403 handling

`ProviderExecutor._github_active_rules` currently delegates to `_json`, which raises on
all non-zero return codes before parsing the response. Both policy discovery and guarded
merge mode selection call this function. Consequently the documented plan-limitation 403
is indistinguishable from a scope or infrastructure failure.

GitHub documents protected branches as available for private repositories with GitHub Pro,
Team, Enterprise Cloud, or Enterprise Server, while GitHub Free provides them for public
repositories. The live response on the incident repository names this exact plan boundary.

Primary sources:

- [GitHub REST: Get rules for a branch](https://docs.github.com/en/rest/repos/rules?apiVersion=2022-11-28#get-rules-for-a-branch)
- [GitHub: About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub CLI: `gh repo create`](https://cli.github.com/manual/gh_repo_create)
- [GitHub CLI: `gh pr merge`](https://cli.github.com/manual/gh_pr_merge)

## Semantic Invariants

1. Remote mutation authority is explicit, immutable, actor/evidence-bound, and persisted
   before mutation.
2. Bootstrap identity binds local repository identity, target owner/name, private
   visibility, base branch, and exact base SHA.
3. Matching replay performs readback first and emits no duplicate creation or push.
4. A remote base branch is published only when absent; an unequal existing SHA is a hard
   contradiction.
5. The policy fallback recognizes one structured provider plan response, not the text
   fragment `403` alone.
6. `feature-unavailable` is live provider evidence, not evidence that checks passed or a
   merge was authorized.
7. Queue mode still requires a successful active-rules observation containing a
   `merge_queue` rule.
8. Every merge mutation remains bound to PR ID and exact head SHA.
9. Existing exact external-merge reconciliation remains available and unchanged.
10. No bootstrap or policy receipt transfers authority to application merge or wiki sync.

## Failure Modes

| Failure | Required result |
|---|---|
| Target repository already exists privately and is empty | Adopt only after exact owner/name/visibility readback. |
| Target repository exists with conflicting visibility or identity | Fail before push. |
| `origin` points elsewhere | Fail without editing the remote. |
| Remote base exists at the authorized SHA | Record idempotent success. |
| Remote base exists at another SHA | Fail without force or overwrite. |
| Crash after creation but before remote configuration | Replay reads the matching repository, configures the absent exact remote, and continues. |
| Crash after push but before receipt persistence | Replay proves exact remote branch/default branch and records success without another mutation. |
| Exact GitHub plan-limitation 403 | Record `feature-unavailable`, empty active rules, and direct mode. |
| Generic or malformed 403 | Open/refresh the provider gate. |
| Successful rules response with merge queue | Preserve queue mutation and intent-bound readback. |
| Head, checks, approvals, or mergeability are not acceptable | Gate as today. |

## Implementation Slices

### Slice 1: Private-Free policy evidence

Introduce a structured active-rules observation. Parse the non-zero JSON response only for
the exact plan-limitation classification, expose it in receipts, and keep all other errors
fatal. Exercise both eligibility and manual exact-head merge paths, plus queue and generic
403 regressions.

### Slice 2: Audited private repository bootstrap

Add a standalone CLI transaction and provider operation with a local append-only intent
record, lock, safe GitHub creation/adoption, exact-base publication, default-branch
readback, crash recovery, contradiction tests, and user-facing documentation.

The bootstrap slice depends on Slice 1 only for delivery ordering, not code semantics; it
may be reviewed independently.

## Verification Strategy

### Unit

- Exact structured plan-limitation response becomes `feature-unavailable`.
- Generic 403, scope errors, malformed JSON, and unexpected documentation URLs fail.
- Successful rules and merge-queue behavior are unchanged.
- Bootstrap intent validation rejects missing or contradictory authority and identity.
- Remote URL normalization cannot equate different owners or repositories.

### Integration

- Simulate direct and queue PRs through the provider executor.
- Simulate every bootstrap crash boundary: pre-create, post-create, post-origin, post-push,
  and post-default-branch update.
- Prove exact replay performs no second create/push and conflicting remote heads never
  force-push.
- Run the full Ticket Autopilot suite.

### Live

- On a private GitHub repository whose plan returns the exact feature-limit response,
  observe `feature-unavailable` and complete an explicitly authorized exact-head merge
  without external UI work.
- If a disposable repository creation is separately authorized, bootstrap it privately,
  verify exact `origin`, base SHA, and default branch, then remove it only through a
  separate human-owned cleanup decision. Without that authorization, the bootstrap claim
  remains simulated-external/deployable-for-test.

## Acceptance Outcomes

- [ ] The exact private-plan rules response no longer opens a provider gate by itself.
- [ ] Arbitrary policy API failures still open a provider gate.
- [ ] Direct and merge-queue behavior retain exact-head and crash-safety guarantees.
- [ ] One explicit command can create/adopt the exact private repository and publish the
      exact first base without an operator shell command.
- [ ] Bootstrap replay and contradictions are persisted, deterministic, and tested.
- [ ] Documentation no longer claims that the human must perform repository creation or
      first-base publication when the exact bootstrap authority was supplied.
- [ ] Generic merge language still does not become manual exact-head or autonomous run
      authority.

## Open Questions

None block implementation. Live repository creation remains a separate provider-side
authorization and verification boundary; local tests must not manufacture it.
