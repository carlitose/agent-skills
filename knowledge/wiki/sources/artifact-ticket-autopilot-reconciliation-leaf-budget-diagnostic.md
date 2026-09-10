---
type: source
title: "Ticket Autopilot Reconciliation Leaf-Budget Exhaustion Bug"
identity_key: artifact:ticket-autopilot-reconciliation-leaf-budget-diagnostic
identity_strength: stable
source_path: docs/specs/ticket-autopilot-reconciliation-leaf-budget-diagnostic.md
source_digest: sha256:464b28a4bc16bc10c067c72f659b614709e60c35fe5ebc48f41896e9cececb79
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-08-28
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Ticket Autopilot Reconciliation Leaf-Budget Exhaustion Bug

Compiled from `docs/specs/ticket-autopilot-reconciliation-leaf-budget-diagnostic.md`. Identity is `artifact:ticket-autopilot-reconciliation-leaf-budget-diagnostic`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-28** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-ticket-autopilot-reconciliation-leaf-budget-lb-01]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-ticket-autopilot-reconciliation-leaf-budget-diagnostic.md","payload_bytes":3462,"payload_sha256":"464b28a4bc16bc10c067c72f659b614709e60c35fe5ebc48f41896e9cececb79"}],"payload_bytes":3462,"payload_sha256":"464b28a4bc16bc10c067c72f659b614709e60c35fe5ebc48f41896e9cececb79","schema":1,"source_digest":"sha256:464b28a4bc16bc10c067c72f659b614709e60c35fe5ebc48f41896e9cececb79","source_identity":"artifact:ticket-autopilot-reconciliation-leaf-budget-diagnostic","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3462,"payload_sha256":"464b28a4bc16bc10c067c72f659b614709e60c35fe5ebc48f41896e9cececb79","schema":1,"source_digest":"sha256:464b28a4bc16bc10c067c72f659b614709e60c35fe5ebc48f41896e9cececb79","source_identity":"artifact:ticket-autopilot-reconciliation-leaf-budget-diagnostic"} -->
```markdown
# Ticket Autopilot Reconciliation Leaf-Budget Exhaustion Bug

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-reconciliation-leaf-budget-diagnostic`
- Role: `spec`
- Standalone: true

### Children

- [LB-01 restore semantic-revalidation leaf capacity](../tickets/ticket-autopilot-reconciliation-leaf-budget/done/01-restore-semantic-revalidation-leaf-capacity.md)

## Type

Diagnostic spec

## Status

Fixed and covered by regression tests in LB-01.

## Diagnosis Report - lens: single-pass

### Root cause

Semantic reconciliation correctly invalidated review, QA, and verification evidence, but
`Kernel._invalidate_leaf_artifacts()` cleared handoffs/results while retaining the prior
CandidateRef's interaction counters and consumed mandatory reservations. A previously
verified ticket could therefore enter a fresh verification cycle with no usable reservation.
The contradiction was between `Kernel.prepare_reconciliation()` and
`leaf_protocol._admit_resources()`.

### Evidence

- The affected WS-04 run entered reconciliation with 7 of 10 interactions consumed and both
  mandatory reservations complete.
- Revalidation retained those counters, then fresh review, QA planning, and QA execution
  reached 10 of 10.
- The canonical verification checkpoint completed bundle construction, validation,
  reduction, and handoff in memory, but admission failed with
  `leaf interaction budget is reserved for mandatory stages`.
- An in-memory replay reproduced the same exception without mutating the ledger.
- The CandidateRef passed 157 LLM Wiki tests, 33 focused runner/skill tests, compilation,
  patch-integrity, and patch-equivalence checks before the admission failure.

### Fix

Budget enforcement now applies to the current semantic CandidateRef epoch. Every semantic
invalidation starts a fresh bounded epoch and clears old mandatory-reservation consumption;
append-only `leaf-result-recorded` history remains the source for truthful lifetime resource
reporting. Equivalent reconciliation keeps its evidence and consumes no capacity.

Existing schema-4 runs use the public `revalidation-budget-repair` transition. It rebuilds
the current epoch from retained CandidateRef-bound progress, records before/after state and
source event sequences, is idempotent, and refuses to erase same-CandidateRef retries. Real
exhaustion is persisted as an actionable `resource-budget` gate.

### Alternatives ruled out

- **Project failure:** candidate-scoped tests and integrity checks passed.
- **Stale bundle or CandidateRef:** checkpoint work reached `handoff-ready` for the exact
  current CandidateRef before budget admission.
- **Missing reservation configuration:** both slots existed, but belonged to the old epoch.
- **Manual ledger repair:** rejected because it bypasses audited transition replay.
- **Reusing old evidence:** rejected because a changed CandidateRef requires fresh validation.

### Confidence: high

The live failure, in-memory replay, persisted history, old admission arithmetic, and passing
post-fix 7-of-10 regression all identify the same mechanism.

## Preserved constraints

- Changed CandidateRefs receive fresh review, QA execution, verification, and merge
  authorization.
- Same-CandidateRef retries remain hard-bounded.
- Lifetime interaction, tool-call, wall-time, invalidation, cache, and failure reporting stays
  truthful.
- Exact-head merge authorization, provider readback, and verification claims are unchanged.

```
