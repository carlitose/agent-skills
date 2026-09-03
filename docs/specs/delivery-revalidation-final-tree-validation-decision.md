# Final-Tree Validation Architecture Decision

## Artifact Graph

- Artifact ID: `artifact:delivery-revalidation-final-tree-validation-decision`
- Role: `spec`
- Parent: [Delivery Revalidation Efficiency Wayfinder](delivery-revalidation-efficiency-wayfinder.md)

### Children

- [FTV-01 — Observe exact tracked completion projections](../tickets/delivery-revalidation-final-tree-validation/done/01-observe-exact-tracked-completion-projections.md)
- [FTV-02 — Persist and recover projected-not-integrated completion](../tickets/delivery-revalidation-final-tree-validation/done/02-persist-and-recover-projected-state.md)
- [FTV-03 — Run one final quality cycle on the exact delivery tree](../tickets/delivery-revalidation-final-tree-validation/done/03-run-one-final-quality-cycle.md)
- [FTV-04 — Prove observation parity and safe rollback](../tickets/delivery-revalidation-final-tree-validation/done/04-prove-observation-parity-and-rollback.md)
- [FTV-05 — Enable the bounded tracked final-tree lane](../tickets/delivery-revalidation-final-tree-validation/05-enable-bounded-tracked-lane.md)

## Type

Architecture decision

## Status

Accepted on 2026-09-02 through the DRV-03 human decision interview. The final confirmation is
bound to `pi-session://01a04e2a-0b7a-70fd-be3b-06500686244a/message/dd22dae2`.

## Decision

Adopt a bounded hybrid with a pre-quality projection lane for one exact ordinary tracked-ticket
case and the current full process for every other topology.

For the eligible lane, the runner performs implementation and simplification against an
implementation CandidateRef `I`, creates and durably binds the exact final delivery CandidateRef
`D`, then runs `review -> qa-plan -> qa-execute -> verify -> finalize` exactly once against `D`.
Commit, push, PR publication, merge, and terminal proof remain later operations.

This decision rejects general post-verification evidence selection. Review, QA, and verification
results from `I` never become results for `D`. Implementation and simplification remain explicit
predecessor lineage, while the complete final quality and final Verification Record bind `D`.

## Evidence

- [DRV-01 current-flow report](../research/delivery-revalidation-current-flow-and-cost.md)
  proves that exact-final-tree identity is mandatory but unconditional broad-suite duplication is
  not itself the invariant. Four completed samples consumed 16 extra leaf interactions and 80
  recorded command/check labels.
- [DRV-01](../tickets/delivery-revalidation-efficiency/done/01-map-current-flow-and-cost.md)
  also records CST-03 as the counterexample: a completion-shaped transition contained runner code
  and test changes, so path shape alone cannot grant the narrow lane.
- [DRV-02](../tickets/delivery-revalidation-efficiency/done/02-prototype-projection-proof-options.md)
  tested 17 frozen positive, negative, crash, replay, ignored-source, reconciliation, and provider
  fixtures across three disposable designs. Every design could fail closed, but none established
  that the production effect inventory is complete.
- [The wayfinder](delivery-revalidation-efficiency-wayfinder.md) records the three design trade-offs.
  Design A avoids a general causal test-selection oracle but changes lifecycle ordering; design B
  preserves ordering by making evidence composition security-critical; design C adds a bounded
  classifier and lane-specific replay.

The available figures are logical command/check labels, not wall-time measurements. This decision
makes no speedup claim.

## Goals

- Bind every final delivery claim to the exact final tree while avoiding a second downstream
  quality cycle for an exact ordinary tracked completion.
- Make lane selection deterministic, versioned, content-addressed, complete over the `I -> D`
  diff, and fail-closed.
- Preserve append-only lifecycle history and crash-safe replay without moving a locally projected
  ticket back to its pending path.
- Preserve the current conservative path for legacy and non-eligible topologies.
- Introduce the behavior first in observation mode with a deterministic return to the full path.

## Non-Goals

- General test-impact analysis or reuse of review, QA, or verification across arbitrary trees.
- Optimization for ignored or external ticket sources, reconciliation, post-commit recovery,
  provider-mutated runs, ambiguous histories, wiki publication, or Pi synchronization.
- Weakening exact-head provider readback, expected-head merge, or fresh terminal reachability.
- Reconstructing projection proofs for historical ledgers.
- Claiming measured wall-time, token, or provider savings.

## Terms

- **Implementation CandidateRef `I`:** the exact tree after implementation and simplification,
  before tracked completion effects.
- **Delivery CandidateRef `D`:** the exact final tree after the allowed completion effects.
- **Ordinary tracked lane:** a tracked pending ticket with no ignored/external source, active
  reconciliation, recovery successor, provider mutation, or ambiguous lifecycle state.
- **Projection manifest:** the canonical complete declaration of every allowed `I -> D` effect.
- **Projected-not-integrated:** a durable local run state where the exact completion projection
  exists in the isolated worktree but no delivery commit, PR, or integration claim exists.

## Semantic Invariants

1. **Exact final identity.** Review, QA, verification, finalization, PR rendering, provider head,
   merge authorization, and terminal proof bind the same `D` lineage.
2. **Complete negative proof.** Eligibility requires the complete sorted path/blob/mode diff and
   proves that no unlisted path, index stage, receipt field, or link edit exists.
3. **No semantic evidence transfer.** Review, QA, and verification on another CandidateRef never
   satisfy a stage on `D`.
4. **Intent before effects.** The runner persists the versioned manifest and expected identities
   before moving a ticket, writing a receipt, or repointing links.
5. **Literal recovery.** Replay resumes named checkpoints or blocks on ambiguity. It never erases
   a persisted projection or rewrites ledger history.
6. **Conservative exclusion.** Missing contracts, unsupported source modes, stale identity,
   tampering, duplicate effects, provider state, or topology ambiguity cannot enter the lane.
7. **Authority separation.** Projection grants no completion-source ownership, merge,
   reconciliation, provider, terminal-proof, wiki, Pi, status-change, cleanup, or reload authority.
8. **Published completion boundary.** Before terminal integration, a problem remains work on the
   original ticket. A regression discovered after integration creates a linked follow-up ticket.

## Eligibility Contract

The runner may select the lane only before completion effects and only when all checks pass:

- the frozen source mode is tracked and the exact pending ticket path, bytes, digest, and mode
  match the run snapshot;
- the ticket has no provider mutation, reconciliation intent, recovery successor, ignored-source
  authority, source-drift gate, or ambiguous prior effect;
- the current index exactly matches `I` and contains no unmerged or extra stage;
- a versioned planner deterministically computes one same-byte/same-mode move to the canonical
  `done/` destination, one canonical completion receipt, and the complete link-repoint closure;
- the planner binds every old and new blob, mode, path, CandidateRef, artifact generation, effect
  key, and the digest of the complete expected diff;
- an independent readback of the resulting index equals the expected manifest and derives `D`;
- the actual complete `I -> D` diff contains no extra or missing row.

Failure before durable intent selects the unchanged full process. Contradiction after intent or
partial effects blocks publication and enters exact recovery; it never silently downgrades or
rolls back.

## Target Lifecycle

1. Complete implementation and simplification and freeze `I`.
2. Evaluate lane eligibility without mutating the worktree.
3. For an excluded case, continue through the current process unchanged.
4. For an eligible case, persist the projection intent and canonical manifest.
5. Apply or replay the exact ticket move, receipt, and link effects once.
6. Read back every effect, prove the complete negative diff, derive `D`, and persist
   `projected-not-integrated` before quality begins.
7. Run `review -> qa-plan -> qa-execute -> verify -> finalize` once against `D`.
8. On a quality failure, keep `D` only in the isolated worktree, keep the original ticket active,
   publish nothing, and resume the failed stage against the same `D`.
9. If later semantic candidate drift changes `D`, invalidate to the earliest causally required
   stage. Extra implementation drift returns to `implement`; projection-only drift returns to
   exact recovery. Neither case moves the ticket back to the pending path.
10. Only a verified `D` may be committed, pushed, rendered, or published as a PR.
11. Merge and terminal proof use their existing exact-head contracts. Post-integration consumers
    remain separate.

## Failure and Recovery

The durable checkpoints are `intent-persisted`, `effects-read-back`, `final-tree-bound`, and
`quality-complete`.

- A crash before intent has no projection effect and resumes normal scheduling.
- A crash after intent re-evaluates the exact source/destination/index state against the manifest.
- Exact partial effects resume without duplication.
- Exact final effects with a missing final binding append that binding once.
- An exact replay after final binding returns `already-applied` without another move or receipt.
- Both paths present, both absent, changed bytes/modes, unexpected links, duplicate effect keys,
  stale CandidateRefs, proof tampering, or provider mutation block before publication.
- A failed review, QA, or verification keeps `projected-not-integrated`; it is not a completed or
  integrated claim.
- A later defect after terminal integration becomes a new linked bug ticket rather than a rewrite
  of the completed ticket.

## Compatibility

Historical runs without the new versioned manifest always retain the current full revalidation
cycle. The runner does not infer or backfill absent effects, timing, evidence segments, or
checkpoints. Existing tracked, ignored, docs-only, reconciliation, recovery, migration,
provider, terminal-proof, wiki, and Pi receipts replay literally.

An in-flight manifest remains bound to its recorded contract version. A configuration rollback
cannot reinterpret or abandon a partially applied projection; exact recovery finishes or blocks
that projection under its original version.

## Rollout and Rollback

The feature has three explicit modes:

- `off`: current behavior only;
- `observe`: compute and persist a candidate eligibility/projection observation while the current
  full lifecycle remains authoritative;
- `enabled`: use the bounded pre-quality lane when the exact contract passes.

The initial release defaults to `observe`. A controlled ordinary tracked run must show identical
planned and authoritative `D`, effect manifest, receipt, link closure, final Verification Record,
and terminal lineage. The frozen positive, fallback, blocked, crash, and replay fixtures must also
remain green. Only then may a separate delivery switch the default to `enabled`.

Rollback changes the default to `off` for new, not-yet-intended projections. Existing durable
intents continue exact replay or fail closed under their recorded version. Rollback never rewrites
history or weakens a gate.

## Security and Under-Testing Response

- The narrow lane does not trust filenames, author identity, docs-only labels, or the presence of a
  ticket move.
- Review, QA, and verification all execute on `D`; there is no general semantic test-selection
  oracle.
- The manifest covers the full index diff, including file mode and negative extra-diff evidence.
- Link repoints require a deterministic complete closure, not only validation of links the planner
  happened to list.
- Any unsupported or ambiguous state excludes or blocks the lane before provider mutation.
- Observation mode compares the prospective lane with the unchanged authoritative behavior before
  enablement.

## External and Authority Contracts

This decision changes only scheduling and completion-projection ordering inside Ticket Autopilot.
It does not change Ticket Envelope v1, CandidateRef v2 identity, provider APIs, merge policies,
repository reconciliation authority, terminal integration proof, wiki-sync ownership, local-Pi
ownership, ticket status transactions, or completion authority for ignored sources.

## Implementation Slices

1. Define the canonical projection manifest, exact planner, validator, negative-diff proof, and
   observation receipt.
2. Add `projected-not-integrated`, named checkpoints, idempotent effects, and literal legacy
   fallback to ledger/kernel replay.
3. Reorder the eligible ordinary tracked lane so completion precedes final review/QA/verification,
   while every excluded topology keeps current behavior.
4. Compose the final `D` Verification Record without importing review, QA, or verification results
   from `I`; preserve exact provider and terminal bindings.
5. Add observation-mode parity evidence, mutation/crash/history tests, rollback behavior, and a
   separate enablement delivery.

## Verification Strategy

### Unit

- Canonical manifest encoding and digesting.
- Exact path/blob/mode planner and deterministic link closure.
- Eligibility exclusions and complete negative-diff validation.
- State transitions, unique effect keys, tamper detection, and mode configuration.

### Integration

- One ordinary tracked ticket reaches `D` before review and completes one final quality cycle.
- Extra paths, changed implementation blobs, ticket mode/bytes, receipt fields, links, source mode,
  reconciliation targets, provider state, or stale identities never use the lane.
- Crashes at every named checkpoint replay once or block on ambiguity.
- Quality failure keeps the original ticket active and unpublishes `D`.
- Candidate drift after projection invalidates to the correct stage without moving the ticket back.
- Historical ledgers replay unchanged and cannot gain a projection proof.

### System and forward tests

- Observation mode compares the prospective and authoritative paths on the same controlled ticket.
- Commit tree, PR body, provider head, expected-head merge, and fresh terminal proof all bind `D`.
- Switching to `off` leaves new runs on current behavior and safely drains existing intents.
- Tracked, ignored, recovery, reconciliation, provider-before/after, wiki, and Pi matrices preserve
  their separate contracts.

### Live and manual

No live provider mutation is required to validate projection safety. A later controlled rollout
may observe a normal provider delivery, but it cannot substitute for deterministic local evidence
or grant merge authority.

## Acceptance Outcomes

- An eligible tracked completion runs one downstream quality cycle, all on `D`.
- A complete manifest proves exactly the ticket move, receipt, link closure, and absence of extra
  effects.
- Every unsupported, stale, tampered, exceptional, or ambiguous case retains current behavior or
  blocks before publication.
- Crash replay is idempotent at every checkpoint and never rolls the ticket path backward.
- Failed final quality publishes nothing and resumes the original ticket against the same `D`.
- Historical runs remain byte- and state-compatible without backfilled proof.
- Observation mode produces deterministic parity evidence before enablement.
- Rollback affects only new projections and preserves in-flight intent truth.
- Every final delivery and terminal claim binds the exact `D` lineage.
- No adjacent authority is inferred or consumed.

## Alternatives Rejected

### Retain unconditional full revalidation

Safest with current machinery, but keeps known duplicate work for a bounded deterministic case.
Retained as the fallback and rollback behavior rather than the default target.

### Proof-carrying post-verification projection

Preserves current ordering but makes evidence segmentation and causal test selection part of the
trusted security boundary. Rejected because the final quality cycle can instead run once on `D`.

### Broad pre-quality projection

Rejected because ignored sources, reconciliation, recovery, provider-mutated runs, and historical
ambiguity do not share one proven completion contract.

## Unresolved Questions

None that changes the selected architecture. Production implementation must still prove that its
effect planner and link closure are complete; failure to prove completeness keeps the feature in
`observe` or `off`.
