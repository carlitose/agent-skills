# Ticket Autopilot Tracked Completion Projection Grant

## Type

Feature and source-ownership hardening spec

## Status

Accepted design. ICP-01 is delivered; ICP-02 reauthorization support is open.

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-tracked-completion-projection`
- Role: `spec`
- Parent: [Ticket Autopilot Ignored Ticket Sources](ticket-autopilot-ignored-ticket-sources.md)

### Children

- [ICP-01 Grant exact tracked completion projections](../tickets/ticket-autopilot-tracked-completion-projection/done/01-grant-exact-tracked-completion-projections.md)
- [ICP-02 Reauthorize an exact completion projection after candidate drift](../tickets/ticket-autopilot-tracked-completion-projection/02-reauthorize-an-exact-completion-projection-after-candidate-drift.md)

## Problem

Ticket Autopilot correctly rejects an ignored ticket source when its candidate or delivery
base starts tracking any original, current, or completion path. That guard prevents an
implicit source-ownership migration. It also rejects a distinct case: a verified candidate
may need its generated outputs to describe the state after its own ignored-source
finalization and therefore track an exact copy only at its canonical `done/` destination.

Run `agent-skills-wiki-ingest-20260829` is the preserved reproduction. AWI-02 reached
CandidateRef tree `7dec2b895d829159fd94d671e849256665fe1a75`; only
`docs/tickets/llm-wiki-agent-skills-ingest/done/02-build-the-tracked-agent-skills-project-wiki.md`
is tracked among that ticket's source paths, and its digest equals the managed source. All
quality stages passed, but delivery correctly stopped before commit at `source-mode-drift`
because no versioned exception or authority existed.

## Goal

Allow one explicitly authorized, exact-digest, candidate-only completion projection without
weakening the general ignored-to-tracked guard, caller-owned finalization, crash recovery,
provider boundaries, or merge authority.

## Non-Goals

- Implicit ignored-to-tracked source migration.
- Tracking the open/current ticket path or arbitrary ignored files.
- Inferring authority from candidate content, AFK mode, access, credentials, silence,
  verification, or generic gate approval.
- Granting ticket start, HITL, finalization, provider, wiki-sync, branch-policy, exact-head,
  or merge authority.
- Changing Ticket Envelope v1 or parsing ticket prose as machine authority.
- Applying a grant to AWI-02 as part of implementation verification.

## Current Behavior

`assert_ticket_source_mode` classifies the original, current, and canonical destination
paths together. Any tracked path makes the observed classification `tracked`. For an
`ignored` run, delivery opens a deterministic `source-mode-drift` gate and requires a new
run from a tracked base. This is correct for tracked open paths and inherited source
publication, but it cannot distinguish an exact candidate-only completion projection.

## Target Contract

### Immutable explicit grant

A dedicated command records an append-only, lock-serialized grant entry for an existing
non-terminal run and ticket. The ordered grant log may contain more than one entry only when
a caller explicitly reauthorizes a later exact CandidateRef; no entry is rewritten or
silently retargeted. Each grant binds:

- schema, repository identity, run ID, and ticket ID;
- managed snapshot manifest digest and ticket digest;
- complete exact CandidateRef;
- canonical `done/<original-name>` destination;
- actor and non-empty durable evidence reference.

Persistence happens before resolving a gate or retrying delivery. An exact replay of any
entry is idempotent. A contradictory replay of the same grant identity fails closed without
rewriting it. Candidate drift makes every old entry inapplicable; only a new explicit command
with a new exact CandidateRef, actor, and durable evidence may append a successor entry.

### Candidate and base validation

A grant may be recorded and used only when all conditions hold:

1. the immutable run source mode is `ignored`;
2. the delivery base still classifies the ticket paths as ignored;
3. neither original nor current open source path is tracked in the candidate;
4. exactly the canonical completion destination is tracked among those paths;
5. the index entry is one regular, non-executable file—not a symlink, submodule, or other
   mode;
6. newline-normalized index-blob content digests to both the managed snapshot ticket digest
   and CandidateRef ticket digest;
7. the canonical caller-owned current source still satisfies existing digest, containment,
   and symlink checks.

Working-tree content is not evidence for candidate bytes; validation inspects the index/tree
blob and mode. A destination already tracked by the delivery base is inherited publication
and remains drift even when its bytes happen to match.

### Existing gate resolution

The operation can run before delivery or against an already opened gate. If a gate exists,
it may resolve only one matching `source-mode-drift` gate whose ticket, tree,
classifications, boundary, and canonical destination agree with the newly validated grant.
It cannot consume a generic approval, another gate category, another candidate, or another
ticket. History records the exact gate transition and grant identity.

### Delivery and finalization

Every existing source-mode guard remains fail-closed by default. At each guarded boundary,
only a current exact grant changes the candidate classification from forbidden promotion to
`completion-projection`; the base remains `ignored`. Delivery may commit that one tracked
`done/` file, while `finalize_done` still runs the ignored caller-owned move and completion
summary transaction before commit/push. Crash replay converges through the existing intent
and applied receipt; completion does not broaden the grant.

No grant is inherited by stacked descendants. Reconciliation that moves the tracked
projection into a descendant's base remains drift. Delivery, PR body, provider readback,
manual/autonomous policy, and exact-head merge checks remain separate and unchanged.

## Semantic Invariants

- Without an exact grant, all current source-mode behavior is byte-for-byte and
  decision-for-decision unchanged.
- The open/current ignored source never enters the candidate.
- A projection contains only the exact normalized ticket source at its canonical completion
  destination.
- The delivery base remains ignored; integrated source publication cannot masquerade as a
  projection.
- Every authority entry is immutable, actor/evidence-bound, candidate-bound, append-only,
  and exact-replay only; a later entry does not alter or broaden an earlier one.
- Grant persistence precedes gate resolution and every newly permitted mutation boundary.
- Ignored source finalization and completion receipts retain their existing ownership and
  crash semantics.
- Projection authority never transfers to finalization, provider, wiki-sync, HITL, or merge
  authority.

## Failure Modes

- Missing, malformed, stale, or contradictory grant.
- Mismatched repository, run, ticket, snapshot, digest, CandidateRef, actor, evidence,
  destination, predecessor order, or grant-log identity.
- Tracked original/current path, extra tracked ticket path, tracked base, or inherited
  projection.
- Non-regular/executable index mode, invalid UTF-8, or digest mismatch.
- Caller source drift, contradictory completion destination, or symlink/path escape.
- Existing gate differs by ticket, path, boundary, classification, or candidate.
- Crash before/after grant persistence, gate resolution, source move, receipt, commit, push,
  or provider readback.

Each fails closed or exactly replays from persisted state. No failure may partially rewrite
an authority record or consume an unrelated gate.

## Security and Data Concerns

The grant deliberately authorizes publishing ticket content that the repository otherwise
ignores. Scope must therefore be narrower than a Git pathspec: one digest-matched regular
blob at one canonical destination for one frozen CandidateRef. Do not read arbitrary ignored
siblings, copy folder contents, follow symlinks, or accept a working-tree/index mismatch.
Actor and evidence are attribution, not authentication; callers must not infer user consent
from tool access.

## Alternatives

- **Remove the tracked projection.** Rejected for candidates whose accepted output must
  truthfully represent post-finalization source disposition.
- **Allow any matching `done/` file automatically.** Rejected because candidate content is
  not source-publication authority.
- **Treat the run as tracked after candidate creation.** Rejected because it silently mutates
  immutable source ownership and breaks caller-owned finalization.
- **Use generic gate approval.** Rejected because a generic approval does not bind the exact
  repository, source digest, candidate tree, destination, or authority limits.
- **Require a new tracked-base run.** Retained as the recovery for actual ownership migration,
  but unnecessarily broad for an explicit exact candidate-only projection.

## Explicit Reauthorization After Candidate Drift

AWI-02 exposed the missing recovery path after ICP-01. Its original grant correctly bound
candidate tree `7dec2b895d829159fd94d671e849256665fe1a75`. Terminal-base repair and wiki progress
refresh produced tree `500a2a0fcde417fefe066d3fccaa9ee196e63b32` while preserving the projected ticket blob
byte-for-byte. The old grant correctly became inapplicable, but the singleton storage model
made a new exact human authorization impossible to record in the same run. Delivery could
only reopen `source-mode-drift` gates forever or abandon the run.

The reauthorization contract is:

1. Existing singleton grants remain readable as the first immutable grant-log entry.
2. `grant-completion-projection` may append a successor only after validating the complete
   current CandidateRef and all existing candidate/base/source constraints.
3. A successor has its own grant identity, actor, durable evidence, predecessor identity,
   and monotonically increasing sequence. It never copies actor/evidence from an older entry.
4. Exact replay of any entry is idempotent. Reusing an identity with different fields,
   reordering entries, deleting history, or mutating an old entry is ledger corruption.
5. Only the newest entry that exactly matches the current CandidateRef may resolve its
   matching gate or authorize a guarded source-mode boundary. Older entries remain audit
   history and confer no current capability.
6. Candidate drift after the newest entry still fails closed and requires another explicit
   authorization. Byte equality, prior consumption, verification, AFK mode, merge authority,
   or machine readback never creates a successor grant.
7. Status and compacted history expose the active grant identity plus immutable predecessor
   lineage without placing unbounded grant documents in every history snapshot.

This is reauthorization capability, not reauthorization itself. ICP-02 implementation and
verification must not append a grant to AWI-02 or resolve its gate. A new exact AWI-02 grant
remains a separate human authority event after ICP-02 is terminally integrated and AWI-02's
post-rebase candidate is frozen.

## Implementation Slice

[ICP-01](../tickets/ticket-autopilot-tracked-completion-projection/done/01-grant-exact-tracked-completion-projections.md)
owns the original grant schema, command, kernel/ledger/history behavior, exact index/base/source
validation, matching gate resolution, guarded-delivery recognition, status/docs, and causal
regression suite.

[ICP-02](../tickets/ticket-autopilot-tracked-completion-projection/02-reauthorize-an-exact-completion-projection-after-candidate-drift.md)
owns the append-only grant log, legacy singleton normalization, successor validation,
active-grant selection, status/history projection, and the repeated-gate recovery tests.

Applying or reapplying the capability to any live run is a separate operator authority event
after the owning implementation is durably integrated.

## Verification Strategy

- Unit tests for grant schema, complete field binding, exact replay, successor append,
  predecessor/order contradictions, legacy singleton normalization, ledger validation,
  history compaction, and status projection.
- Disposable Git integration tests inspecting index modes/blobs for valid projection,
  ungranted projection, tracked open/current paths, extra paths, non-regular/executable modes,
  stale trees, digest mismatch, and tracked-base inheritance.
- Gate tests proving only the newest exact matching source-mode gate is resolved after durable
  successor persistence, while old entries remain inapplicable.
- Crash tests around grant persistence, gate resolution, ignored source finalization, receipt,
  commit, and provider boundaries.
- Full simulated delivery proving one exact projection in the commit, canonical ignored source
  moved with summary, PR-body handoff unchanged, and no merge attempt.
- Existing tracked/ignored parity, full Ticket Autopilot suite, forward scenarios, static and
  diff checks, artifact-audit delta, and controlled context ceiling.
- Reproduction proving an old exact grant plus candidate drift can accept a new explicit
  successor and stop repeated equivalent gates, while byte equality alone still cannot.
- No live provider, merge, or AWI-02 grant claim from implementation evidence.
