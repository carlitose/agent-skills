---
type: source
title: "Ticket Autopilot Semantic Reconciliation PR-Body Rebind Bug"
identity_key: artifact:ticket-autopilot-semantic-reconciliation-pr-body-rebind-diagnostic
identity_strength: stable
source_path: docs/specs/ticket-autopilot-semantic-reconciliation-pr-body-rebind-diagnostic.md
source_digest: sha256:5d72f8fc291a37ca33f80ab22a9b0cfb05a491d9036eba914d21651a1a1d843a
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-08-28
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Ticket Autopilot Semantic Reconciliation PR-Body Rebind Bug

Compiled from `docs/specs/ticket-autopilot-semantic-reconciliation-pr-body-rebind-diagnostic.md`. Identity is `artifact:ticket-autopilot-semantic-reconciliation-pr-body-rebind-diagnostic`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-28** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-ticket-autopilot-semantic-reconciliation-pr-body-rebind-rb-01]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[13],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/artifact-ticket-autopilot-semantic-reconciliation-pr-body-rebind-diagnostic.md","payload_bytes":5217,"payload_sha256":"5d72f8fc291a37ca33f80ab22a9b0cfb05a491d9036eba914d21651a1a1d843a"}],"payload_bytes":5217,"payload_sha256":"5d72f8fc291a37ca33f80ab22a9b0cfb05a491d9036eba914d21651a1a1d843a","schema":1,"source_digest":"sha256:5d72f8fc291a37ca33f80ab22a9b0cfb05a491d9036eba914d21651a1a1d843a","source_identity":"artifact:ticket-autopilot-semantic-reconciliation-pr-body-rebind-diagnostic","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | 13: Verification |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":5217,"payload_sha256":"5d72f8fc291a37ca33f80ab22a9b0cfb05a491d9036eba914d21651a1a1d843a","schema":1,"source_digest":"sha256:5d72f8fc291a37ca33f80ab22a9b0cfb05a491d9036eba914d21651a1a1d843a","source_identity":"artifact:ticket-autopilot-semantic-reconciliation-pr-body-rebind-diagnostic"} -->
```markdown
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

```
