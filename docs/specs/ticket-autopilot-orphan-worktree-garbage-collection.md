# Ticket Autopilot orphan-worktree garbage collection

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-orphan-worktree-garbage-collection`
- Role: `spec`
- Parent: [Agent Skills repair-to-Omicron work queue](agent-skills-repair-to-omicron-wayfinder.md)

### Children

- [WGC-01 — Register ownership and plan orphan cleanup](../tickets/ticket-autopilot-orphan-worktree-garbage-collection/done/01-register-and-plan-orphan-cleanup.md)
- [WGC-02 — Apply an exact guarded cleanup plan](../tickets/ticket-autopilot-orphan-worktree-garbage-collection/done/02-apply-exact-guarded-cleanup-plan.md)

## Type

Architecture specification.

## Status

Accepted for implementation after WDT-01. The implementation is local and provider-free;
it grants no remote, publication, merge, Pi synchronization, or reload authority.

## Context and evidence

Ticket Autopilot creates isolated worktrees beneath
`.<repository-name>-ticket-autopilot-worktrees/<run-id>`, then stores the absolute worktree
path and base SHA in the integrity-protected run ledger. Its existing single-run `cleanup`
command acquires the run lock, rejects running runs, checks every ticket mutation boundary,
rejects dirty worktrees and unpublished commits, removes the worktree without `--force`, and
preserves the ledger.

That contract is safe when an operator already knows one exact run ID. It does not safely
answer which of many accumulated worktrees are runner-owned, inactive, unreferenced, and
eligible for collection. Path shape alone is not ownership proof. A terminal code run may
also retain an open tracked-wiki delivery, a failed Pi-sync transaction, or another durable
reference that must remain visible even when its code PR is merged.

Primary implementation anchors:

- `ticket-autopilot/scripts/autopilot/git_ops.py` owns isolated worktree creation, managed-path
  checks, cleanliness checks, retained-head checks, and non-force removal.
- `ticket-autopilot/scripts/autopilot/ledger.py` owns integrity-protected ledgers and
  process-crash-releasing non-blocking run locks.
- `ticket-autopilot/scripts/autopilot/cli.py` owns the single-run cleanup transaction and its
  administrative gates.
- `ticket-autopilot/tests/test_cli.py` pins rejection of running, dirty, and unpublished
  cleanup candidates.

## Goals

- Persist explicit, content-addressed ownership for every newly created runner worktree.
- Allow exact, actor/evidence-bound adoption of a legacy worktree only when its valid ledger,
  Git registration, repository identity, run ID, base SHA, and managed path all agree.
- Produce a durable, provider-free cleanup plan that classifies every owned worktree as
  `eligible` or `protected` with deterministic reason codes.
- Remove only the exact eligible entries in an unchanged plan after a complete second
  preflight, while preserving ledgers, manifests, artifacts, branches, remotes, and provider
  state.
- Make interruption replayable through intent-first, per-entry applied receipts.

## Non-goals

- Deleting worktrees discovered only by name or path pattern.
- Pruning Git worktree metadata, using `git worktree remove --force`, deleting branches,
  resetting files, or discarding dirty/untracked content.
- Querying or mutating a provider during planning or application.
- Inferring that a PR, tracked-wiki delivery, Pi sync, reconciliation, or merge gate is closed.
- Cleaning failed, aborted, waiting, running, locked, ambiguous, or malformed runs.
- Cleaning temporary wiki projection worktrees, exact-source checkouts, protected canonical
  project roots, local Pi checkouts, or worktrees owned by another Git common directory.
- Retrofitting ownership silently or treating Break Glass or `pi-code-tool` autoapproval as
  cleanup authority.

## Domain model

### Ownership manifest

A `worktree-owner-v1` manifest is an integrity-protected record stored in the owning run
directory. It binds exactly one run ID to:

- the canonical Git common directory and locally configured normalized remote identity; a
  local-only run uses the exact non-authoritative `unconfigured / absent` sentinel, while a
  syntactically safe unsupported test remote uses `local-or-unsupported` plus only its
  SHA-256 identity;
- the canonical worktree path and its Git administrative directory;
- the run's base SHA and ticket-source manifest digest;
- the ownership origin (`created-by-run` or `legacy-adoption`);
- for adoption, the actor, durable evidence, and exact source-ledger SHA-256.

The manifest is immutable. Unknown fields, malformed hashes, path aliases, symlink traversal,
duplicate claims, or identity disagreement invalidate ownership rather than weakening it.
Creation persists the manifest as part of run setup. If setup cannot persist or read back the
manifest, it compensates by removing only the still-clean detached base worktree; otherwise it
fails visibly and leaves the directory unmanaged.

### Protected candidate

An owned worktree is `protected` when any required fact is absent, malformed, changing, or
unsafe. Protection includes, at minimum:

- a held run lock or a run state other than `completed`;
- any ticket not durably `integrated`, any open gate, or cleanup already in an ambiguous state;
- a current code PR record not durably read back as merged;
- a tracked-wiki record whose latest durable delivery is not `merged` or `unchanged / no-diff`;
- a Pi-sync intent without an exact completion receipt;
- a repository reconciliation, final-tree, Git merge/rebase/cherry-pick/revert/bisect, or other
  interrupted mutation;
- dirty tracked, staged, ignored, or untracked content;
- a locked/prunable Git worktree entry, symbolic path, identity mismatch, unexpected branch or
  HEAD, an unretained commit, or any reference from another nonterminal run;
- the primary worktree, invocation checkout, current working directory, an explicit protected
  path, or any path outside the exact managed parent.

`Protected` is a successful planning outcome, not a cleanup error. The plan reports all reason
codes without claiming process liveness beyond the observed run lock and durable state.

### Eligible orphan

An owned worktree is eligible only when every protection check passes, the owner ledger is
integrity-valid and terminally completed, all durable local delivery projections are terminal,
the worktree is clean and unlocked, its HEAD is retained by the ledger's exact integration
proof, and no other active record requires the path. The owner manifest and historical ledger
remain referenced; “unreferenced” means no other live operational record needs the checkout.

### Cleanup plan

`worktree-gc-plan-v1` is a canonical JSON document written under the repository Git common
directory at `ticket-autopilot/worktree-gc/plans/<plan-sha256>.json`. It contains repository
identity, the complete Git worktree inventory digest, every validated ownership-manifest and
ledger digest, observed path/HEAD/branch/cleanliness state, exact eligible entries, protected
entries and reason codes, explicit protected paths, and its self-consistent content digest.

Planning may inspect local Git and acquire run locks non-blockingly. It makes no provider call
and mutates no worktree or run ledger. Repeating it over unchanged state returns the same plan.

### Cleanup application

`worktree-gc-apply-v1` requires the plan path, exact plan SHA-256, actor, and durable evidence.
Application:

1. validates the complete plan schema and digest before interpreting paths;
2. acquires a repository GC lock and all eligible run locks in deterministic order;
3. recomputes the complete plan and requires byte-equivalent safety inputs;
4. performs a full preflight for every entry before the first deletion;
5. persists an intent that binds the plan digest and exact ordered entry set;
6. removes each worktree with ordinary `git worktree remove`, never `--force`;
7. reads back both filesystem absence and Git-registration absence;
8. records the existing ledger cleanup transition and an immutable per-entry receipt; and
9. completes with a digest-bound summary receipt.

A stale plan removes nothing. After intent, replay uses the same plan and intent: already
applied entries must have exact receipts and readback; remaining entries are revalidated before
continuation. A contradiction stops visibly without deleting another entry. Deletion does not
rewrite Git integration or erase diagnostic evidence.

## Public commands

- `worktree-owner-adopt <run-id> --expected-ledger-sha256 <sha> --actor <actor> --evidence <evidence>`
- `worktree-gc-plan [--protect <absolute-path>]...`
- `worktree-gc-apply <plan-path> --expected-plan-sha256 <sha> --actor <actor> --evidence <evidence>`

All commands resolve repository ownership through the Git common directory. Adoption and
application are local mutation boundaries. Plan output clearly states that eligibility is not
a provider, merge, publication, Pi-sync, or reload claim.

## Failure modes

- Missing or invalid ownership proof: ignore the unmanaged worktree and report it separately;
  never adopt or delete it by pattern.
- Manifest/ledger/Git disagreement, duplicate ownership, symlink, or cross-repository identity:
  protect and report the exact contradiction.
- Run lock busy, state drift, dirty content, interrupted Git operation, or changed inventory:
  protect during planning or reject the entire stale application before deletion.
- Provider-relevant state lacks a terminal local readback: protect; do not query the provider.
- Removal or readback fails after intent: preserve intent and prior receipts, stop, and require
  exact replay after the cause is corrected.
- Ledger cleanup recording fails after directory removal: preserve the applied receipt with
  the pre-removal ledger digest and reconcile only through exact replay; never recreate or
  claim an untouched worktree.

## Security and data safety

Paths are absolute, canonical, component-wise symlink-safe, and constrained to the one managed
parent derived from the bound repository root. JSON schemas reject unknown fields. Digests use
canonical UTF-8 JSON. User-controlled paths never select arbitrary deletion targets. Commands
do not use shell interpolation, `--force`, broad glob deletion, Git reset, branch deletion, or
provider APIs. Actor/evidence identify local authority but do not authorize any other boundary.

## Implementation slices

1. Add immutable ownership manifests, explicit legacy adoption, deterministic inventory, and
   provider-free plan classification with adversarial path/state coverage.
2. Add exact-plan application, all-entry preflight, intent/receipt replay, ordinary Git removal,
   ledger cleanup recording, and interruption/idempotence coverage.

## Verification strategy

### Unit

- Canonical schema/digest validation, unknown-field rejection, normalized identity, path and
  symlink checks, deterministic reason ordering, and terminal-record classification.
- Exact adoption binding and refusal of malformed, duplicate, active, or mismatched claims.
- Intent and applied-receipt schema, replay, and contradiction checks.

### Integration

- Create multiple linked worktrees spanning completed, running, waiting, dirty, locked,
  detached-unretained, branch-unretained, open-wiki, incomplete-Pi-sync, cross-referenced, and
  unmanaged cases; prove only the complete eligible set is planned.
- Change every safety input between plan and apply and prove zero removals.
- Interrupt after one removal, then replay and prove exact idempotent completion with preserved
  ledgers and no branch/remote deletion.
- Prove a completed run with WDT-01-shaped `pr-open` wiki state and incomplete Pi sync remains
  protected.

### Regression

Run the complete Ticket Autopilot suite, CLI contract tests, compile checks, `git diff --check`,
and artifact graph audit. No live provider test is required because the feature is explicitly
provider-free.

## Acceptance outcomes

- Newly created run worktrees have exact ownership manifests; legacy ownership requires an
  explicit digest-bound adoption command.
- Planning is deterministic, provider-free, and classifies unsafe or ambiguous worktrees as
  protected with machine-readable reasons.
- Application cannot remove anything from a stale or partially valid plan.
- Only certainly runner-owned, completed, clean, unlocked, retained, operationally unreferenced
  worktrees are removed, without force.
- Ledgers, manifests, branches, remotes, provider records, candidate stores, Pi state, and
  diagnostic artifacts are preserved.
- Interrupted application is evidence-preserving and idempotently replayable.
