# Merge authority and reconciliation

Load only for this operational branch. [Ticket Autopilot](../SKILL.md) owns scheduling; this
reference owns this branch's operator procedure. CLI `<command> --help` remains the syntax
authority.

## Contract

`run --merge-policy autonomous --merge-actor <identity> --merge-evidence <durable-ref>` creates a
standing grant with the run. For an existing non-terminal manual run, `grant-autonomous-merge <run>
--repo <repository> --actor <identity> --evidence <durable-ref>` appends the same immutable
run-bound authority exactly once; identical replay is idempotent, while conflicting authority or
unresolved merge mutation fails closed. The grant binds repository, run, ticket-set digest,
provider, and policy. Before mutation, reread live exact head, checks/rules, approval, and
mergeability, then merge atomically by expected head. Non-passing, simulated, queue-uncertain, or
unsupported results gate. Only a proven GitHub queue may use `enqueuePullRequest(expectedHeadOid)`
with intent-bound readback and no direct fallback.

An unambiguous affirmative repository-wide “merge all”, “merge everything”, or “mergia tutto”
instruction for one known repository enters this flow. Inspect `repository-autonomous-merge-status`
first. If authority is absent, the human actor and durable affirmative message supply the operator
decision for `grant-repository-autonomous-merge --repo <absolute-repository> --scope
current-and-future-runs --actor <identity> --evidence <durable-ref>`; if an exact grant is already
active, preserve and use it rather than replacing its provenance; revoked, legacy, malformed, or
contradictory state fails closed. Then invoke `merge-all --repo <repository>`. Do not request a
caller-supplied PR head SHA or narrow the instruction to one displayed PR. The append-only grant
binds the exact Git common directory, provider, and normalized remote; the observing worktree is
context, not authority identity, so linked worktrees share it while independent clones do not.
`merge-all` discovers each live head itself, discovers canonical run ledgers, adopts the grant only
for merge-ready manual runs, and drives each independently eligible PR through the unchanged
expected-head path; future runs adopt at the same boundary. Quoted text, examples, questions,
negations, revocations, policy requests, regression reports, or an ambiguous repository identity
grant nothing. An already-provider-merged PR may instead be reconciled as `external-readback` only
when a fresh terminal proof succeeds; this records history and grants no provider mutation
authority. `revoke-repository-autonomous-merge` serializes revocation before any later provider
mutation. Run-local grants are never overwritten, and non-merge gates, conflict content, force push,
code changes, publication, bootstrap, source/finalization, wiki, Pi, visibility, history rewrite,
and cleanup authority remain separate.

`grant-repository-autonomous-reconciliation --repo <absolute-repository> --scope
current-and-future-runs --actor <identity> --evidence <durable-ref>` persists a second,
independently revocable schema-2 Git-common authority; it is never inferred from chat or merge
authority. Schema-1 merge or reconciliation state remains inspectable but unusable until
`migrate-repository-authority --kind <merge|reconciliation> --expected-state-sha256
<exact-file-sha256> --actor <identity> --evidence <durable-ref>` records intent before replacement,
preserves predecessor grant/revocation history, and returns an idempotent readback receipt. Sibling
worktrees report `legacy-binding-migration-required`; irrelevant legacy reconciliation state no
longer blocks ordinary manual implementation. `resume` and `merge-all` may apply only the run-local
`artifacts/autonomous-reconciliation/<ticket-id>.json` proposal bound to the active grant, exact
repository/remote, ticket digest/CandidateRef, old remote/local head and tree, old/new target
SHA/tree, sorted Git-observed conflict paths, canonical resolution digest, and exact result tree.
Recreate the real rebase, modify only unresolved index paths, reject markers/extra paths/drift,
persist adoption before mutation, persist application readback, and force normal fresh CandidateRef
review, QA, verification, finalization, PR-body, provider, and merge eligibility afterward.
`revoke-repository-autonomous-reconciliation` blocks unapplied proposals and later dependent
mutation; it grants no semantic choice, implementation, source, bootstrap, wiki, Pi,
provider-policy, or merge authority.

## Operator procedure

## Manual and autonomous merge policy

`manual` is the default. A ticket's `execution_mode: AFK` means it can proceed
without interactive implementation decisions; it is **not merge consent**.
Credentials, write access, silence, or an absent response are not consent
either.

Autonomous merge is opt-in for a whole run and requires an actor plus durable
evidence. It can be selected at creation time:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  run docs/tickets/my-change --repo . --provider github --provider-mode live \
  --run-id autonomous-my-change --merge-policy autonomous \
  --merge-actor "alice@example.com" \
  --merge-evidence "artifact://change-123/autonomous-run-grant"
```

A non-terminal run created with the manual default can receive that authority
later without rewriting its ledger or approving every PR separately:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  grant-autonomous-merge my-change --repo . \
  --actor "alice@example.com" \
  --evidence "artifact://change-123/autonomous-run-grant"
```

The command appends one immutable grant under the run lock and immediately
continues an eligible open PR through the normal autonomous path. Exact replay
with the same actor and evidence is idempotent. Terminal runs, conflicting
authority, and unresolved provider merge mutations fail without replacing the
grant or contacting the provider.

The immutable grant is bound to the repository, run, ticket-set snapshot,
provider, and policy version. It replaces only the per-PR prompt. Before every
merge attempt the runner still verifies the frozen semantic candidate, reads the
current PR/head and provider policy live, checks required checks and approvals,
and uses only an operation atomically pinned to that head. Pending, failed,
unknown, simulated, stale-head, unsupported-provider, or unproven merge-queue
results gate instead of weakening the operation.

### Repository-wide merge-all

For one repository-level decision across current and future runs, persist a
separate Git-common authority and process every independently merge-ready PR:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  grant-repository-autonomous-merge --repo "$PWD" \
  --scope current-and-future-runs \
  --actor "alice@example.com" \
  --evidence "artifact://change-123/repository-merge-grant"
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  merge-all --repo "$PWD"
```

Schema-2 grants bind the Git common directory, provider, and normalized remote. The
observing checkout is recorded only as context: linked worktrees share the authority,
while an independent clone with the same remote has none. `merge-all` discovers only
canonical run ledgers, adopts the
grant only when a manual run already has a validated merge-ready PR, and routes
each PR through the existing live exact-head critical path. A later run adopts
the same active authority automatically when it reaches that boundary. If a PR is
already provider-merged, `merge-all` may record only read-only historical truth
when the exact head or explicit provider merge commit is freshly reachable from
the recursively derived terminal branch; that path does not consume a merge
mutation. Run-local autonomous grants are not overwritten. Non-merge gates are
reported and left untouched; merge-all never implements or chooses conflict content,
bootstraps repositories, synchronizes a wiki or Pi, or changes visibility. A separate
repository reconciliation grant may apply an already-materialized exact conflict proposal;
it does not widen merge authority.

Revoke before any later provider mutation with separate actor/evidence-bound
provenance:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  revoke-repository-autonomous-merge --repo "$PWD" \
  --actor "alice@example.com" \
  --evidence "artifact://change-123/repository-merge-revocation"
```

Grant, adoption, exact replay, and revocation are append-only. The authority
lock establishes a deterministic order between revocation and an expected-head
provider mutation. Historical integration is never rewritten, and a revoked
grant cannot be silently replaced.

Legacy schema-1 authority remains inspectable but cannot be consumed. An original
checkout reports its legacy active/revoked state and migration availability; a sibling
reports `legacy-binding-migration-required`. Migrate exactly one kind only after
separately authorizing the observed state-file SHA-256:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  migrate-repository-authority --repo "$PWD" --kind merge \
  --expected-state-sha256 <exact-file-sha256> \
  --actor "alice@example.com" \
  --evidence "decision://change-123/migrate-merge-authority"
```

The transaction validates the legacy checkout/common-directory/provider/remote
binding, persists immutable intent before atomic replacement, retains predecessor
grant and revocation provenance, and returns an idempotent receipt. Repeat separately
with `--kind reconciliation` only under distinct migration authority. Wrong digests,
remotes, common directories, kinds, symlinks, or contradictory replay fail without
widening authority. Irrelevant legacy reconciliation state does not block ordinary
manual implementation; any merge-all or proposal-consumption path still fails closed
until its required authority kind is migrated.

### Repository-wide autonomous reconciliation

Conflict-resolution authority is a second, opt-in Git-common record:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  grant-repository-autonomous-reconciliation --repo "$PWD" \
  --scope current-and-future-runs \
  --actor "alice@example.com" \
  --evidence "decision://change-123/repository-reconciliation"
```

The grant is repository/provider/remote/actor/evidence-bound, integrity-wrapped,
hash-linked, revocable, and never inferred from chat. A covered run looks only for
`artifacts/autonomous-reconciliation/<ticket-id>.json` under its Git-common run
directory. The proposal binds the exact ticket digest/CandidateRef, old remote/local
heads and trees, old/new targets, sorted Git-observed conflict paths, resolution-blob
digest, and result tree.
The runner reapplies the real rebase, changes only those unresolved index paths,
requires exact tree equality, records separate adoption/application receipts, and
then invalidates stale semantic evidence through the normal quality pipeline.

`resume` and `merge-all` discover a matching proposal programmatically. Missing,
stale, ambiguous, extra-path, marker-bearing, corrupt, or revoked proposals remain
gated. Publication, provider readback, checks, approvals, mergeability, and exact-head
merge still require the separate merge authority and their normal fresh evidence.
Revoke future application and dependent mutation with:

```bash
python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" \
  revoke-repository-autonomous-reconciliation --repo "$PWD" \
  --actor "alice@example.com" \
  --evidence "decision://change-123/repository-reconciliation-revoked"
```

On a private repository whose GitHub plan does not provide branch rules, the
active-rules API returns a structured 403 saying that GitHub Pro or a public
repository is required. The adapter accepts only that exact status, message, and
rules-endpoint documentation URL as live `feature-unavailable` evidence. It
records an empty active-rule set and direct mode without relaxing either merge
path: autonomous merge still proves the exact head, mergeability, checks,
approvals, and run grant; manual merge still requires exact-head authority and
uses no provider-policy bypass. Every generic/malformed 403, scope error, or
other policy readback failure still gates; a successfully observed merge-queue
rule still forbids direct fallback.

## Stacked pull requests and evidence reuse

Stacking is limited to a single-parent chain. A ticket with several blockers
waits until all of them are integrated instead of creating a multi-parent stack.
Integration always targets the recursively inherited root delivery base, not an
immediate parent branch. Provider `MERGED` therefore remains non-integrated when
a child head and provider merge object exist only on an obsolete stack branch;
a fresh proof may reconcile it later if that exact object reaches the terminal
branch. When a parent merges or an ordinary parentless PR's recorded base advances, the
runner guards the PR's recorded remote head, derives the old anchor and target
from delivery lineage, rebases it, pushes with force-with-lease, retargets its
PR, publishes a new head-bound body, and reads the provider state back before
considering merge eligibility again. Parentless reconciliation never invents a
dependency solely to enter this path.

Quality evidence is bound to semantic CandidateRef v2: base tree OID, candidate
tree OID, normalized ticket digest, and contract version. Commit, branch, PR,
base, and head lineage are tracked separately. If reconciliation changes only
lineage while all four semantic fields remain exactly equal, prior review, QA,
verification, cache identity, and claim ceiling are preserved; provider checks
are still rerun for the new head, and a one-shot manual approval is cleared. A
changed base tree, candidate tree, ticket digest, or contract version forces the
complete quality loop again. Remote divergence, an unproposed or inexact rebase
conflict, unresolvable trees, or contradictory retarget/readback evidence always gates.
An active repository reconciliation grant can consume only an exact proposal that
reproduces the observed conflict set and result tree; it never selects semantics itself.

See the implemented decisions for
[autonomous stacked delivery](../../docs/specs/ticket-autopilot-autonomous-stacked-delivery.md),
[ignored ticket sources](../../docs/specs/ticket-autopilot-ignored-ticket-sources.md),
[tracked completion
projections](../../docs/specs/ticket-autopilot-tracked-completion-projection.md),
and the
[merge critical path](merge-critical-path-v1.md).
