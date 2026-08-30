# Repository-wide autonomous reconciliation authority

## Artifact Graph

- Artifact ID: `spec:ticket-autopilot-repository-autonomous-reconciliation`
- Role: spec
- Standalone: true

### Children

- [RAR-01 — Add persistent repository autonomous reconciliation authority](../tickets/ticket-autopilot-repository-autonomous-reconciliation/01-add-persistent-repository-autonomous-reconciliation-authority.md)

## Type

Feature specification with bug-prevention intent.

## Decision

Ticket Autopilot will represent the operator's standing instruction to resolve eligible
delivery-reconciliation conflicts as explicit machine-readable repository state, not as
conversation memory. This authority remains separate from repository-wide autonomous merge
authority: merge authority permits an exact-head provider merge, while reconciliation
authority permits a bounded resolution proposal to be applied to a previously verified
candidate after its delivery base advances.

The repository grant applies to current and future runs bound to the exact repository. It is
actor/evidence-bound, append-only, integrity-wrapped, lock-serialized, revocable, and rechecked
before applying a proposed resolution and before any later provider mutation. Once activated,
the runner must not ask again for a covered reconciliation gate merely because a new session or
agent lacks chat history.

## Current behavior and defect

Repository-wide `merge-all` authority is already persisted programmatically, but it deliberately
grants no conflict-resolution authority. When an eligible PR becomes conflicting after `main`
advances, the runner can produce an exact resolution proposal but must request a new human gate
approval. The decision can therefore exist only in conversation or in one gate-specific artifact.
A later session correctly remembers merge authority yet cannot prove standing reconciliation
authority.

The safety separation is correct; the missing capability is a second persistent authority source.
Widening `merge-all` implicitly would erase that boundary and make audit/revocation ambiguous.

## Goals

- Persist one explicit repository-wide autonomous reconciliation grant for current and future
  runs.
- Make the grant discoverable and enforceable by the runner without relying on chat history.
- Cover only delivery reconciliation of an already verified candidate onto an advancing target.
- Require a disposable exact resolution proposal before mutating the owning run worktree.
- Bind proposal application to exact base, old/new heads and trees, conflict paths, proposed tree,
  patch digest, actor, evidence, and policy version.
- Revalidate the resulting CandidateRef through the normal quality and delivery pipeline before
  push, retarget, or merge.
- Compose with repository `merge-all` so a covered conflict can progress without another prompt.
- Support append-only revocation and immediate pre-mutation authority rechecks.

## Non-goals

- Widening the existing repository merge grant or overwriting run-local grants.
- Blindly choosing arbitrary implementation behavior or claiming tests prove product intent.
- Resolving implementation-time conflicts, source ownership, completion projection, bootstrap,
  wiki, Pi, cleanup, visibility, secrets, or provider policy gates.
- Applying a proposal after its target, remote head, ticket digest, CandidateRef, conflict set, or
  repository identity changes.
- Force-pushing without the existing expected-remote compare-and-swap and provider readback.
- Treating AFK mode, credentials, silence, or free-form chat as machine-readable authority.

## Authority contract

Add explicit commands:

```text
ticket-autopilot grant-repository-autonomous-reconciliation \
  --repo <absolute-repository> \
  --scope current-and-future-runs \
  --actor <identity> \
  --evidence <durable-ref>

ticket-autopilot revoke-repository-autonomous-reconciliation \
  --repo <absolute-repository> \
  --actor <identity> \
  --evidence <durable-ref>
```

The grant binds the canonical repository, Git common directory, provider and normalized remote,
fixed scope, actor/evidence, schema and policy version, grant ID, sequence, and content digest.
State lives under Git common Ticket Autopilot state in an integrity envelope with hash-linked
append-only events and its own repository lock. Exact replay is idempotent; contradiction,
corruption, path redirection, symlink state, or repository mismatch fails closed.

Revocation is ordered under the same lock. It prevents every not-yet-applied resolution and every
later provider mutation that depends on repository reconciliation authority. Historical receipts
remain immutable.

## Covered reconciliation

A standing grant may be adopted only when all of these are true:

1. the ticket was verified and has recorded live PR/delivery lineage;
2. the runner created a durable base-advance or stack reconciliation intent before provider
   mutation;
3. the target advanced and automatic rebase produced only a bounded reconciliation conflict;
4. no push, retarget, queue, or merge mutation for the replacement head has started;
5. a disposable clone/worktree produced a canonical proposal document containing the exact old
   remote head, old local head/tree, old and new target SHA/tree, conflict paths, candidate patch
   digest, proposed result tree, and retained evidence references;
6. proposal paths are confined to the Git-observed conflict set, while non-conflicting changes are
   Git-derived from the frozen candidate and exact new target;
7. the authority is still active immediately before applying the exact proposal tree; and
8. the owning run worktree reproduces the proposed tree byte-for-byte before the gate is consumed.

The runner appends an adoption and proposal-application receipt rather than manufacturing a human
gate approval. A different proposal tree, target refresh, remote-head drift, extra path, unresolved
marker, or missing receipt requires a new proposal. Semantically ambiguous or validation-failing
results remain gated even with authority.

## Programmatic orchestration

`merge-all` and normal autonomous resume paths inspect both repository authority sources. Merge
authority continues to own provider mutation. Reconciliation authority allows the scheduler to:

1. classify the exact reconciliation conflict;
2. produce and validate a disposable proposal;
3. adopt the active repository reconciliation grant into the run by grant ID/digest;
4. apply only the exact proposed tree and record readback;
5. invalidate stale evidence and run the normal review, QA, verification, finalization, PR-body,
   expected-remote push, provider readback, and fresh merge-eligibility flow; and
6. continue into repository `merge-all` without another conversational prompt.

Run-local authority remains authoritative for runs that already have a distinct grant. Repository
revocation is checked again before force-with-lease publication, retarget, and exact-head merge so
adoption cannot make revocation ineffective.

## Semantic invariants

1. Chat history is never the authority database.
2. Merge and reconciliation are separate grants, receipts, locks, status fields, and revocations.
3. A grant authorizes a bounded process, not an unknown future tree without proposal proof.
4. Proposal application precedes fresh CandidateRef evidence; old evidence cannot be relabeled.
5. Provider mutation remains impossible until the resulting exact head is revalidated and read
   back.
6. A moved target or remote head invalidates the proposal before mutation.
7. Exact replay produces no duplicate adoption, application, push, retarget, or merge.
8. Ambiguity, failing quality, unsupported conflict shape, or authority corruption stays visible as
   a gate.
9. Existing repository merge authority and run-local grants remain byte-for-byte compatible.
10. Status and `merge-all` report the authority/grant ID, adopted proposal digest/tree, revocation,
    and any uncovered or failed gate.

## Failure modes

| Failure | Required result |
|---|---|
| No active reconciliation grant | Preserve the existing explicit conflict gate. |
| Exact grant replay | Return the existing grant without duplicate history. |
| Grant contradiction/corruption/path escape | Fail before candidate mutation. |
| Proposal target or remote head drift | Discard as stale and derive a new proposal. |
| Proposal includes non-conflict paths | Reject without applying it. |
| Applied worktree tree differs from proposal | Abort/recover to the guarded old local head. |
| Quality or verification fails | Keep the new candidate gated; do not publish. |
| Revocation races with application/push | Repository lock orders the operations and the later one observes revocation. |
| Crash after adoption but before application | Replay revalidates authority and proposal; no duplicate mutation. |
| Crash after application | Read back exact tree and resume fresh evidence, never reuse stale evidence. |
| Crash after provider mutation | Existing expected-head external reconciliation owns recovery. |

## Security and data concerns

- Proposal and authority state must be regular no-follow files below the canonical Git common
  Ticket Autopilot directory.
- Evidence is provenance, not authentication, and must not include secrets.
- Conflict diagnostics and patches use the existing redaction and bounded-artifact policies.
- The proposal must not infer that unknown content is safe and must not publish new unreviewed
  paths outside the candidate/new-base conflict set.
- Provider credentials, branch protection, checks, approvals, and mergeability remain fresh live
  boundaries.

## Compatibility

The capability is opt-in. Existing repositories, repository merge grants, and run-local grants
retain their current semantics. No existing conflict gate is consumed merely by upgrading code.
Activation requires the new explicit repository command after integration.

## Implementation slice

One tracer-bullet ticket owns:

- repository reconciliation grant/revoke state, locking, integrity, and status;
- proposal schema, canonical digest, exact-tree/path/base/head validation, and crash replay;
- run adoption/application receipts without fabricated human approval;
- autonomous resume and `merge-all` composition;
- revocation rechecks before run-worktree and provider mutation;
- CLI/docs/context updates; and
- disposable conflict, corruption, drift, ambiguity, crash, full regression, and forward tests.

## Acceptance outcomes

1. After one explicit repository grant, two existing runs and one future run can apply eligible
   exact reconciliation proposals without another human prompt.
2. A new session reaches the same decision from repository state alone.
3. A proposal reproduces one exact tree and then triggers fresh CandidateRef evidence before any
   publication.
4. Target/head/path/tree drift, corruption, unsupported conflicts, and failed quality remain gated.
5. Revocation blocks later application and provider mutation, including previously adopted runs.
6. Repository merge authority remains separate and exact-head provider checks remain unchanged.
7. Status and `merge-all` expose deterministic applied, gated, stale, revoked, skipped, and
   failed-before-mutation outcomes.

## Verification strategy

### Unit

- Grant/revoke integrity, exact replay, contradiction, symlink/path, lock, and repository binding.
- Proposal canonicalization and exact base/head/path/tree/digest validation.
- Adoption/application receipt replay and revocation checks.

### Integration

- Disposable real Git repositories with automatic and conflicting rebases.
- Multi-run current/future adoption, exact tree reproduction, semantic invalidation, quality
  revalidation, expected-remote push simulation, and crash recovery.
- Target/remote drift, extra-path, marker, ambiguity, and revocation races.

### Regression

- Full Ticket Autopilot and extension tests, forward scenarios, static checks, artifact-audit delta,
  and controlled context measurement.

### Live boundary

Activation and real provider mutation are separate post-integration operations. Simulated provider
evidence cannot claim a live push, retarget, or merge.
