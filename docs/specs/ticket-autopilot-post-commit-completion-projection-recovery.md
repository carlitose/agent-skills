# Ticket Autopilot Post-Commit Completion-Projection Recovery

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-post-commit-completion-projection-recovery`
- Role: `spec`
- Standalone: true

### Children

- [PCR-01 Resume an exact projection after a runner-authored delivery commit](../tickets/ticket-autopilot-post-commit-completion-projection-recovery/01-resume-an-exact-projection-after-a-runner-authored-delivery-commit.md)

## Type

Bug-analysis spec

## Status

Implemented; verification open.

## Diagnosis Report - lens: single-pass

### Root cause

`finalizer._grant_allows_completion_projection()` already treats `HEAD` as a special runner
delivery boundary: it validates the current exact grant and index against the ignored
CandidateRef base rather than requiring the runner-authored delivery commit itself to remain
ignored. `Kernel.resolve_completion_projection_gate()`, however, accepts only a persisted gate
whose literal `base_classification` is `ignored`. After an earlier delivery commit contains the
projection and the candidate later drifts, source-mode revalidation records `base_classification:
tracked`; a fresh successor can validate and persist but cannot resolve that exact gate. The two
boundaries encode different base semantics for the same recovery path.

### Evidence

- ICP-02 is terminally integrated through PR #170 at terminal SHA
  `33eaac64affc29145a305c02756ff5ddb479e302` and adds append-only successor grants.
- AWI-02 is frozen at CandidateRef base tree
  `cdf80a27866c7d32241ffa12b26e4f7789031061`, candidate tree
  `500a2a0fcde417fefe066d3fccaa9ee196e63b32`, and ticket digest
  `bcf621d93e163aae5997ee8e30ee85a1a9675bacfe0dfd5589be98ead1b340ae`.
- Read-only `inspect_completion_projection()` succeeds for that candidate against its ignored
  CandidateRef base and observes the exact canonical same-digest regular projection.
- Read-only `assert_ticket_source_mode(..., base_ref="HEAD")` fails because AWI-02's
  runner-authored unintegrated branch head tracks the projection; gate
  `gate:AWI-02:dynamic:5` records `observed=tracked` and `base=tracked`.
- The worktree head tree `ecc993e64786e796d01ffeb3c07ea4404b9f810f` equals the prior
  exact prepared CandidateRef tree in the run ledger. The final staged candidate adds 25
  digest-bound wiki refresh files and retains the exact projected ticket blob
  `89605c9edc16444488c55cb1b42e8665f683707b`.
- The integrated terminal branch does not track the AWI-02 destination. The tracked base is the
  run's own unintegrated prepared delivery head, not an integrated ancestor.

### Feedback loop built

Load the preserved AWI-02 ledger and worktree read-only. The following two calls produce the
split deterministically:

1. `inspect_completion_projection(..., expected_tree_oid=<current candidate>,
   base_ref=<CandidateRef base>)` passes.
2. `assert_ticket_source_mode(..., base_ref="HEAD")` raises `SourceModeDriftError` with
   `base_classification: tracked`.

A disposable regression must recreate the same sequence: exact grant A, runner delivery commit
containing projection A, candidate-B drift staged above that commit, a tracked-base source gate,
and explicit successor B.

### Fix location and approach

Keep tracked integrated and reconciled bases forbidden. Add one durable resolution proof for the
narrow runner-authored prepared-delivery-head case. Under the run lock, the grant CLI must:

1. perform all existing exact candidate/base/path/blob/mode/source validation against the
   ignored CandidateRef base;
2. if the sole matching open source gate reports a tracked base, prove the current branch/HEAD
   is the run's own prior prepared delivery head by binding its branch, runner-shaped commit
   message, parent SHA/tree, and HEAD SHA/tree to persisted delivery metadata, the prior prepared
   CandidateRef, the same ticket digest, and ignored base lineage;
3. prove the terminal/provider base does not supply the tracked projection and that no integrated
   or external ancestor is being treated as runner-owned;
4. persist a schema-versioned, content-addressed delivery-head proof with the gate resolution;
5. let kernel and ledger replay accept the tracked-base gate only with that exact proof and the
   newest current grant.

Crash before resolution leaves the successor grant durable and the gate open; replay must rebuild
the same proof or fail closed. Later delivery boundaries continue to re-run the existing exact
index/source checks. No proof may authorize candidate drift, a different head/tree, a fetched or
integrated tracked base, or any adjacent action.

### Alternatives ruled out

- **Request the AWI-02 successor now.** Rejected: it would persist exact authority and then fail
  to resolve the already recorded tracked-base gate.
- **Treat every tracked base as valid.** Rejected: it would weaken ICP-01's explicit prohibition
  on inherited or integrated tracked-base authority.
- **Reset or force-push AWI-02 manually.** Rejected: that would bypass exact reconciliation,
  candidate, review, and authority provenance.
- **Infer recovery from byte equality or the prior grant.** Rejected: neither creates a new human
  authorization or proves runner ownership of the tracked head.
- **Rewrite the existing gate to say ignored.** Rejected: mutable historical observations would
  hide the literal tracked-head condition and break replay.

### Confidence: high

The preserved live run, exact tree/blob identities, direct function-level reproduction, and
opposing hardcoded base semantics identify one deterministic mismatch.

## Goals

- Resume a candidate with a fresh exact successor only when its tracked `HEAD` is a proven
  runner-authored unintegrated prepared delivery head from the same run and ignored base lineage.
- Keep the tracked-base observation auditable rather than rewriting it.
- Make crash/replay behavior deterministic and self-validating.
- Unblock AWI-02 only after this repair is terminally integrated and a separate exact human grant
  is supplied.

## Non-Goals

- Granting, appending, replaying, or resolving AWI-02 authority during implementation.
- Accepting tracked terminal, fetched, reconciled, provider, or unrelated branch bases.
- Resetting, rebasing, force-pushing, or otherwise changing AWI-02.
- Weakening completion projection path, digest, mode, containment, source, or CandidateRef checks.
- Granting finalization, provider, wiki, reconciliation, merge, branch-policy, start, or conflict
  authority.
- Fixing the independent precompleted-parent lineage replay defect.

## Semantic Invariants

- The newest exact completion-projection grant remains necessary but insufficient.
- A tracked-base gate is resolvable only with a fresh durable proof of one exact runner-owned
  prepared delivery head in the same run/ticket/base lineage.
- CandidateRef base classification remains ignored; integrated tracked bases remain fatal drift.
- The terminal branch must not supply the projected ticket destination.
- Grant persistence precedes proof-bound gate resolution.
- Proof identity binds repository, run, ticket/digest, snapshot, grant ID/sequence, CandidateRef,
  destination, gate ID/details, branch, HEAD SHA/tree, parent SHA/tree, runner commit message,
  prior prepared CandidateRef, terminal branch/SHA/tree observation, and proof version.
- Exact replay is idempotent; changed proof, head, tree, gate, grant, candidate, base, or terminal
  observation fails before effects.
- The proof carries no authority outside this one gate transition.

## Failure Modes

- Missing or stale prior prepared delivery metadata.
- Current branch, HEAD SHA, HEAD tree, prior prepared tree, or ignored base lineage mismatch.
- Destination absent from the candidate, wrong mode/blob/digest, or present in the terminal base.
- Multiple/mismatched source gates, non-current grant, malformed lineage, or proof identity drift.
- Crash after grant persistence and before proof/gate persistence.
- Replay after branch, terminal base, candidate, source, or gate drift.

Every failure leaves the gate open and performs no provider, branch, finalization, wiki, or merge
mutation.

## Implementation Slice

PCR-01 owns the proof schema/builder, CLI readback, kernel gate matching, ledger replay/status,
disposable post-commit regression, docs, context update, and complete Ticket Autopilot delivery.
Applying the repaired capability to AWI-02 remains a later separate actor/evidence event.

## Verification Strategy

- Unit tests for proof canonicalization, exact replay, malformed fields, grant/gate/candidate/head
  mismatch, terminal-base projection rejection, and ledger history tamper.
- Real-Git disposable integration reproducing grant A, delivery commit A, staged candidate B,
  tracked-base gate, successor B persistence, proof-bound resolution, and successful guarded
  source boundary.
- Negative real-Git cases for integrated/fetched tracked bases, arbitrary local heads, stale prior
  prepared metadata, changed branch/head/tree, and multiple gates.
- Crash injection before/after successor save and proof-bound gate transition.
- Full Ticket Autopilot tests, forward scenarios, static/diff checks, artifact-audit delta, and
  controlled context ceiling.
- Read-only AWI-02 ledger hash before/after implementation proving no grant or gate mutation.
