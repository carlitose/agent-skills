# Ticket Autopilot Semantic Reconciliation PR-Body Rebind Bug

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-semantic-reconciliation-pr-body-rebind-diagnostic`
- Role: `spec`
- Standalone: true

### Children

- [RB-01 accept a fresh verified bundle after semantic reconciliation](../tickets/ticket-autopilot-semantic-reconciliation-pr-body-rebind/done/01-accept-fresh-verified-bundle.md)

## Type

Diagnostic spec

## Status

Resolved by RB-01

## Diagnosis Report - lens: single-pass

### Root cause

Semantic stack reconciliation correctly invalidates the old CandidateRef evidence, increments
the artifact generation, and requires a new verification bundle. The finalizer correctly
validates the newly rendered PR body against that fresh handoff. The ledger then rejects the
new receipt because `_pr_body_rebind_is_closed()` requires `bundle_sha256`, `bundle_path`, and
`verification_audit_root` to equal the previous PR-body receipt. A semantically changed
candidate cannot both produce a fresh bundle and preserve the old bundle hash and path, so the
revalidation contract and the append-only transition are incompatible.

### Evidence

- `Kernel.prepare_reconciliation()` emits `reconciliation-revalidation-required` for a
  semantic change, moves the ticket back to `review`, increments `artifact_generation`, and
  invalidates prior leaf artifacts.
- Ledger validation for `reconciliation-revalidation-required` requires that new generation
  and active review state, confirming that fresh verification is intentional.
- `Finalizer._validated_render_record()` accepts a render only when its bundle equals the
  current verified handoff bundle. `accept_reconcile_render_payload()` then creates a schema-2
  receipt that retains the complete old receipt in `lineage_rebinds`.
- `_pr_body_rebind_is_closed()` nevertheless required the current bundle hash, bundle path,
  and verification-audit root to equal the previous receipt. The resulting ledger error was
  `delivery-recorded PR-body rebind is not append-only`.
- A pure helper reproduction returned `True` when the rebound receipt reused the old bundle
  and `False` when only the bundle hash and path changed to a fresh bundle.
- `test_autonomous_stack_reconciles_new_head_and_merges_child_without_revalidation` covers the
  lineage-equivalent path. It intentionally keeps the semantic CandidateRef and bundle, so it
  could not detect this semantic-revalidation defect.

### Feedback loop built

A deterministic CLI regression now drives an open stacked PR through semantic reconciliation,
fresh verification, fresh PR-body rendering, a crash before ledger save, exact replay, and
simulated provider readback. A focused closure test rejects stale handoffs, stale CandidateRefs,
missing lineage, receipt mutation, and schema downgrade.

### Fix location and approach

The reconciliation render request now binds the canonical digest of the freshly validated
bundle. The schema-2 lineage entry closes over both the old and new bundle identities while
retaining the complete old receipt. The ledger accepts the changed bundle only when the request
also matches the current CandidateRef, artifact generation, verified bundle artifact, verified
handoff, and exact new head.

An exact legacy reconciliation request that predates the bundle digest is upgraded through the
normal audited delivery-metadata transition. Contradictory legacy requests still fail closed;
no ledger is forced or edited by hand.

### Alternatives ruled out

- **Project or Model Eval failure.** The contradiction occurs in runner receipt validation
  after project verification and before provider publication.
- **A stale caller-supplied bundle.** The finalizer already requires byte-equivalence with the
  current verified handoff before constructing the receipt.
- **Removing append-only lineage validation.** The old receipt, old head, old body hash, and
  new request remain closed and tamper-evident; only the false same-bundle requirement changed.
- **Reusing the old verification bundle.** That would violate semantic candidate invalidation
  and could attach stale evidence to a changed CandidateRef.

### Confidence: high

The original contradiction is covered at both the pure ledger boundary and the complete local
Git/provider-simulation path. Equivalent reconciliation remains covered separately and does not
consume new quality work.

## Constraints

- Preserve D6 candidate invalidation and exact-current-head merge authorization.
- Preserve the complete old PR-body receipt as append-only lineage.
- Accept only the bundle from the current validated verification handoff.
- Keep equivalent lineage-only reconciliation behavior unchanged.
- Do not force, rewrite, or manually patch an affected run ledger.

## Verification

- Focused ledger, finalizer, semantic-candidate, verification, provider-body, forward-matrix,
  and CLI tests pass.
- The complete ticket-autopilot suite reports 434 passing tests and the same three pre-existing
  `wait-what` inventory/policy failures reproduced on the unmodified branch.
- Provider readback is simulated against a real local bare Git remote; no live provider,
  Model Eval, Groq, or deployment call is claimed.
