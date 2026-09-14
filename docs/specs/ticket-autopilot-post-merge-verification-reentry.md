# Post-merge source verification reentry

## Artifact Graph
- Artifact ID: `spec:ticket-autopilot-post-merge-verification-reentry`
- Role: `spec`
- Standalone: true

### Children
- [PMV-01 — Verify merged source without reopening delivery](../tickets/postmerge-verification-reentry/done/01-verify-merged-source.md)

## Type and status
Bug analysis and correction. Execution authorized; merge of this correction and subsequent
pi-personal-config alignment requested separately in the same user conversation.

## Facts and reproduction
An integrated predecessor retains its historical CandidateRef. Its successor is `gated`, has
no stage or CandidateRef, and has an open `post-merge-verification` dynamic gate. The gate
records an exact changed merge commit/tree, historical CandidateRef, and required fresh
candidate binding, review, QA plan/execution and verification. Its `human_canary_approval` is
false. The successor's human start approval is already passed; it does not authorize canary.

On independent in-memory copies of that ledger:
- activation rejects the successor because it is not ready;
- implementation candidate adoption rejects because no implement stage is active;
- candidate invalidation rejects because no ticket is active.

Verification Audit correctly requires a runner-provided current CandidateRef and normalized
ticket input. Operator-generated identities, copied historical passes, or approving the gate
merely to permit activation are not substitutes. The clean integrated runner at `a9810b1`
can read the consumer ledger; unrelated uncommitted installed-runner repairs are not required
for this reader and are excluded from this change.

## Goal
Provide a normal, provider-free, gate-scoped quality entry point for the exact merged source.
Collect fresh verification of the integrated predecessor without reopening it, implementing
the gated successor, weakening the release barrier, or pretending the old source was verified.

## Decision
A post-merge verification session belongs to the existing technical gate, not to either
ticket's delivery lifecycle. Reuse CandidateRef v2, canonical ticket snapshots, schema-3 leaf
validation, configured budgets, and Verification Audit's validator/reducer. A small dedicated
module owns the session contract and progression; CLI and ledger adapters own Git readback
and atomic persistence. Do not add a second scheduler, generic approval system or ticket format.

The public surface must support binding/status, review, QA plan/execution, and canonical
verification. The exact CLI/event spelling is an implementation choice documented by help.

### Binding
- Operate only on the exact open, ticket-scoped dynamic `post-merge-verification` gate.
- Require its versioned source head/tree and historical CandidateRef. Resolve one integrated
  dependency of the gated successor whose historical candidate matches; reject ambiguity.
- Obtain that predecessor's normalized identity, criteria and immutable Ticket Envelope
  reference through the runner's snapshot owner, not Markdown rediscovery.
- Use a clean, registered source worktree in the same Git common directory. Read the exact
  commit and tree with replacement objects disabled; require the gate's recorded head/tree.
  Reading this worktree conveys no mutation or cleanup ownership.
- Freeze a new CandidateRef with the historical base tree and ticket digest, but the newly
  observed source tree. Bind the source worktree, gate, predecessor, normalized input and
  verification scope. Do not replace either ticket's existing CandidateRef or lineage.
- Expose the frozen context through the normal runner interface for inline skill composition.
  Every subsequent accepted result must recheck source and identity. Drift fails closed.

### Quality and completion
- Require fresh `review -> qa-plan -> qa-execute -> verify` results for the new CandidateRef.
  Implementation/simplification assessments required by the audit must also describe this
  frozen source truthfully; old stage outcomes cannot be promoted into the new session.
- Use the existing leaf protocol's validation, isolation, phases, causal quality records,
  artifact hashes and budget behavior. Count actual work, retain failed/partial results, reserve
  QA execution and verification, and do not reset the same-candidate budget on replay.
- The session's normalized scope is post-merge verification of the predecessor's implementation,
  not acceptance of the successor's future proposal or deployment.
- Invoke the canonical Verification Audit validator/reducer; do not duplicate claim policy.
  Require exact candidate, ticket, criteria and accepted stage bindings. Corrupt, stale,
  incomplete or contradictory evidence must not close the gate. Verification of the offline
  source does not require or manufacture a live/canary/production claim.
- Only a valid, complete fresh quality result can resolve this exact technical gate, with a
  durable verification receipt. Human approval alone must not bypass this condition.
- Preserve predecessor state, disposition, old candidate, delivery lineage and historical
  outcomes. Preserve the successor's null/unstarted implementation candidate and all other
  gates. After technical resolution, ordinary scheduling may make the successor ready; this
  is not implementation completion, canary authorization, merge or deployment.

## Persistence and compatibility
Introduce an explicit versioned session record using normal locked ledger transitions and
content-addressed artifacts. Preserve old history verbatim. Existing schema-4 ledgers and the
already-recorded version-1 post-merge gate are an explicitly required compatibility case;
opening a session is an explicit operation, never an automatic migration on read.

Persist before reporting effects. Exact repeats are idempotent and re-observe the source;
interrupted operations resume the trusted prefix. Reject retargeting, contradictory replay,
unknown shapes, forged completion, stale artifact bodies and unrelated gate mutations.
A read-only status call remains pure. Failed preparation must not create a passing gate.

## Boundaries and non-goals
- No provider calls, merge mutation, branch rewrite, retained-host access, credentials, live
  application/provider traffic, DNS, policy changes, installation or interactive Pi reload.
- No reopening integrated tickets or treating changed trees as equivalent.
- No hand-editing the consumer ledger or installed runner, reusing prior break-glass authority,
  importing historic quality as fresh, or admitting unreviewed local changes into this PR.
- No general purpose operational workflow engine, automatic gate approval, or canary feature.
- Preserve unrelated changes in the canonical repository, installed cache and personal config.
- Updating pi-personal-config must follow this correction's durable integration and pin the
  exact integrated commit through its own ordinary delivery and guarded update path.

## Acceptance criteria
1. Reproduce the gated/null-candidate dead end with real disposable Git objects and canonical
   ticket/ledger setup; the new public path emits a runner-owned exact-source context while
   both ticket lifecycles and the technical gate remain unchanged.
2. Accept the clean registered exact source only; reject wrong common repository, dirty
   source, replacement-object spoofing, wrong commit/tree, ambiguous predecessor, malformed
   gate, held/canceled/paused scope, or other contradictory prerequisites before mutation.
3. Reject old-candidate, cross-ticket, out-of-order, partial-as-complete, false independence,
   and exhausted-budget results; retain truthful partial/failure evidence and exact replay.
4. Reject unvalidated or tampered verification/artifact bindings and attempts to approve the
   technical condition without its fresh proof. A valid canonical audit resolves only that
   gate and leaves the integrated predecessor and all live/human gates untouched.
5. Exercise persisted restart/replay and semantic history validation. Existing ledgers remain
   loadable without rewrites and status reads consume no budget or heartbeat.
6. Full runner/verification regressions, forward scenarios, static checks, context-budget and
   Artifact Graph delta checks pass or expose explicit environment limitations. No live claim
   is derived from their local fixtures.
7. Document the trigger, public invocation and scope/claim ceiling behind a focused reference.
   Demonstrate consumer recovery only after integration and approved local alignment; do not
   edit its ledger or install the unmerged implementation as a shortcut.

## Verification strategy
Use real temporary Git repositories and on-disk ledger/artifact round trips at public
boundaries. Keep provider, canary and installer effects absent (or failing sentinels), not
mocked successful. Unit-test the session invariant and reuse the canonical validator/reducer
rather than a permissive test double for the positive end-to-end quality case. Test negative
cases independently so each rejects for its intended cause. Include the new scenario in the
existing forward-test inventory and retain evidence class/limitations.

## Implementation slice
One AFK ticket owns the whole gate/session/source/evidence invariant, its adapters, tests and
operator reference. These changes overlap state and artifact ownership and must not be split
into parallel implementation units. Work serially inline; shared-context review is disclosed.
