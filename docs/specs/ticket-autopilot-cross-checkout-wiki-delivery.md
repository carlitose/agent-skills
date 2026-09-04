# Ticket Autopilot cross-checkout wiki delivery

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-cross-checkout-wiki-delivery`
- Role: `spec`
- Parent: [LLM Wiki Docs-Only Auto-Sync](llm-wiki-docs-only-autosync-wayfinder.md)

### Children

- [WDT-01 — Deliver tracked wiki candidates through the canonical target](../tickets/ticket-autopilot-cross-checkout-wiki-delivery/done/01-deliver-through-canonical-wiki-target.md)

## Type

Bug-analysis specification.

## Status

Accepted for immediate AFK correction after the MRA-01 post-integration reproduction. The
change is limited to Ticket Autopilot's tracked `wiki-sync-v1` delivery and exact local
recovery boundary.

## Observed behavior

MRA-01 ran in a clean independent clone and integrated successfully. The Agent Skills wiki
binding names the persistent canonical project root
`/Users/carlogiuseppesergi/Projects/.agent-skills-runner-latest`, while the exact integrated
source was materialized as a detached worktree of that canonical repository. Compilation
correctly created candidate tree
`e4ebf28d2b269f895f8ecbccf2f04d71270d3a73d46e9bf704720e62e034e2cf`
under the canonical Git common directory with zero lint errors.

The runner then called `deliver_tracked_candidate()` with the independent run clone as
`repo`. The candidate's stable `wiki_identity` points beneath the canonical project root, so
`_wiki_relative(repo, wiki_identity)` returned `delivery-invalid: tracked wiki candidate is
outside the project repository`. This occurred before remote lookup or provider mutation.

The earlier exact-source checkout work intentionally kept path-specific wiki binding strict.
That decision is still correct: a linked or independent run checkout must not become binding-
equivalent to the canonical project path. The missing behavior is in the delivery caller,
which assumes the run repository is also the canonical wiki destination.

## Root cause

The post-integration runner persists run provenance and the exact source head, but it does not
persist a distinct canonical delivery target. `sync_project` already separates canonical
project root, physical source worktree, logical wiki identity, tracking owner, and candidate
owner. `drive_post_integration_sync` collapses them back into one `repo` argument for both
source checkout and tracked delivery.

As a result, any safe isolated run whose configured wiki is path-bound to another checkout can
either fail compilation at `broken-binding` or compile canonically and fail delivery at
`delivery-invalid`. Terminal failure is correct for an unproven destination, but the runner
has no bounded public transaction for validating the destination or retrying a pre-provider
terminal record.

## Goals

- Resolve one canonical wiki delivery target independently from the run checkout.
- Keep the exact-source checkout and path-specific binding contracts unchanged.
- Bind the target before provider mutation to canonical project root, wiki-relative path, Git
  common directory, provider, normalized remote, WikiSyncRef, candidate tree, manifest, and
  validation receipt.
- Permit a run in an independent clone only when its provider and normalized remote exactly
  match the canonical destination repository and the validated result names that destination.
- Materialize the branch and PR from the canonical destination repository without mutating its
  protected checkout.
- Preserve manual versus autonomous wiki authority. Run/code merge authority never transfers.
- Add an explicit exact-record retry transaction for a terminal pre-provider wiki-delivery
  failure, preserving the complete prior record and requiring actor/evidence authority.
- Recover and publish the frozen MRA wiki candidate only after the repaired runner is
  integrated and the exact retry transaction succeeds.

## Non-goals

- Treating two checkout paths as the same wiki binding.
- Allowing arbitrary external candidate paths or cross-remote publication.
- Moving, copying, or rebinding the protected wiki.
- Retrying provider-ambiguous, PR-open, pushed, authorized, merged, or partially published
  records.
- Reusing implementation verification for generated wiki content.
- Granting provider, merge, reconciliation, cleanup, local Pi, or reload authority.
- Repairing unrelated terminal runs or changing LLM Wiki compilation output.

## Target contract

### Canonical delivery target

A tracked `candidate-created` result may carry or derive a versioned delivery target containing:

- canonical project root;
- canonical Git common directory;
- normalized provider and remote;
- safe wiki-relative path;
- WikiSyncRef and candidate tree SHA-256;
- manifest and validation-receipt SHA-256.

The canonical project root comes from the exact compatible wiki binding, not from caller input
alone. It must exist as a real Git worktree root. The logical wiki identity must be a regular
path beneath it. The frozen candidate must be beneath that root's Git common candidate store.
The run repository and destination must resolve to the same provider and normalized remote;
different remotes, providers, absent remotes, symlinks, path escapes, submodules, malformed
bindings, or contradictory state fail before provider observation.

The runner persists and reads back the target receipt before invoking tracked delivery.
`deliver_tracked_candidate` receives the canonical destination repository explicitly. Existing
same-repository delivery remains the degenerate case where run and destination roots match.

### Exact terminal retry

A public local command accepts run, ticket, expected SHA-256 of the complete current wiki-sync
record, actor, and durable evidence. It may return a terminal pre-provider record to
`delivery-pending` only when:

- the ticket is durably integrated;
- the result is the same validated `candidate-created` candidate;
- delivery failed only because the destination was unrepresentable by the old caller;
- no branch, PR, provider receipt, authorization, merge intent, or merge outcome exists;
- the repaired target resolver validates the exact canonical destination;
- the active record matches the caller's digest.

The transaction persists intent before replacement, embeds the full previous record and target
receipt, writes atomically, reads back, and is idempotent. `status` exposes its disposition.
It performs no provider operation. A later ordinary `resume` remains responsible for
publication and merge under the pre-existing wiki policy.

### Compatibility

Backward compatibility is opt-in only for complete persisted `wiki-sync-v1` candidate results
that predate the target receipt. They may derive the receipt from their exact WikiSyncRef,
`wiki_identity`, manifest, and repository readback through the retry transaction. Other legacy,
partial, or malformed records remain terminal.

## Semantic invariants

- Run provenance, source checkout, canonical project, logical wiki, candidate owner, delivery
  repository, and authority are distinct identities.
- Canonical-target resolution never searches home directories, siblings, mounts, or the
  network; it consumes the exact bound path already present in the validated result.
- No path identity is made worktree-stable by Git history alone.
- Cross-checkout delivery is same-provider and same-normalized-remote only.
- Candidate bytes, manifest, validation receipt, changed paths, and WikiSyncRef remain
  immutable during target resolution and retry.
- Protected run, source, and canonical worktrees remain byte-identical.
- Provider mutation still requires the existing exact autonomous wiki grant or later exact-
  head manual authorization.
- A failed sync or delivery never rewrites the integrated ticket outcome.

## Failure modes

| Condition | Outcome |
|---|---|
| Canonical target and run repository are the same | Existing delivery behavior |
| Canonical target is distinct but same provider/remote | Persist target receipt and deliver there |
| Target path, wiki-relative path, or candidate store escapes | Terminal `delivery-invalid` |
| Provider or normalized remote differs | Terminal `cross-repository-identity` |
| Manifest, receipt, candidate, or WikiSyncRef drifts | Terminal `stale-tree` |
| Target checkout is dirty | Protected bytes remain unchanged; use isolated delivery worktree |
| Retry record digest differs | No mutation, exact stale-record error |
| Prior provider/PR/authorization state exists | Retry forbidden |
| Exact retry replay | Same receipt, no additional mutation |

## Implementation slice

`WDT-01` owns one tracer bullet: canonical target resolution and receipt, target-aware tracked
delivery, exact local retry CLI, status/documentation, negative identity tests, and the MRA
production recovery. No second ticket is needed because resolver, retry, and delivery must be
verified as one security boundary.

## Verification strategy

- **Unit:** canonical target derivation, path/common-directory checks, provider/remote
  normalization, receipt digest, legacy candidate adoption, and retry state validation.
- **Integration:** independent run clone plus canonical destination with the same remote;
  compile/freeze at the canonical target and publish through an injected provider while all
  protected worktrees remain unchanged.
- **Negative:** different remote/provider, symlink, path escape, candidate outside target common
  directory, malformed manifest/receipt, stale record digest, absent candidate, and every prior
  provider/authorization state.
- **Recovery:** replay the frozen MRA record provider-free through the exact retry command; only
  after integration use ordinary resume and existing wiki authority.
- **Regression:** full Ticket Autopilot and LLM Wiki suites, exact-source tests, verification
  contract, extensions, compileall, exact-tree diff/readback, and Artifact Graph comparison.

## Acceptance outcomes

- The independent-clone reproduction reaches target-bound tracked delivery instead of
  `broken-binding` or `delivery-invalid`.
- Wrong target identities still fail before any provider observation.
- The exact retry command restores only the eligible MRA-shaped pre-provider terminal record,
  preserves its bytes and provenance, and never publishes by itself.
- Existing same-repository wiki delivery remains unchanged.
- The MRA candidate can subsequently be published and merged by ordinary runner flow, followed
  by exact integrated-source no-diff replay.
