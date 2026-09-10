---
type: source
title: "Ticket Autopilot Delivery Stale Local Base Bug"
identity_key: artifact:ticket-autopilot-delivery-stale-local-base-diagnostic
identity_strength: stable
source_path: docs/specs/ticket-autopilot-delivery-stale-local-base-diagnostic.md
source_digest: sha256:278cc07850437ac04a476d27e08360ba5988185ad1883d2eab143442c9e2b70a
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-08-29
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Ticket Autopilot Delivery Stale Local Base Bug

Compiled from `docs/specs/ticket-autopilot-delivery-stale-local-base-diagnostic.md`. Identity is `artifact:ticket-autopilot-delivery-stale-local-base-diagnostic`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-29** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-ticket-autopilot-delivery-stale-local-base-fs-01]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-ticket-autopilot-delivery-stale-local-base-diagnostic.md","payload_bytes":5196,"payload_sha256":"278cc07850437ac04a476d27e08360ba5988185ad1883d2eab143442c9e2b70a"}],"payload_bytes":5196,"payload_sha256":"278cc07850437ac04a476d27e08360ba5988185ad1883d2eab143442c9e2b70a","schema":1,"source_digest":"sha256:278cc07850437ac04a476d27e08360ba5988185ad1883d2eab143442c9e2b70a","source_identity":"artifact:ticket-autopilot-delivery-stale-local-base-diagnostic","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":5196,"payload_sha256":"278cc07850437ac04a476d27e08360ba5988185ad1883d2eab143442c9e2b70a","schema":1,"source_digest":"sha256:278cc07850437ac04a476d27e08360ba5988185ad1883d2eab143442c9e2b70a","source_identity":"artifact:ticket-autopilot-delivery-stale-local-base-diagnostic"} -->
````markdown
# Ticket Autopilot Delivery Stale Local Base Bug

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-delivery-stale-local-base-diagnostic`
- Role: `spec`
- Standalone: true

### Children

- [FS-01 bind delivery branch creation to the verified base](../tickets/ticket-autopilot-delivery-stale-local-base/done/01-bind-delivery-branch-to-verified-base.md)

## Type

Diagnostic spec

## Status

Fixed and covered by FS-01 regression tests.

## Diagnosis Report - lens: single-pass

### Symptom

A long-lived AFK run completed verification for WS-07, but delivery opened a
`finalization-environment` gate. Git refused:

```text
git switch -c <delivery-branch> main
Your local changes to the wayfinder would be overwritten by checkout.
```

The candidate was not dirty or stale. Its staged tree still matched the verified CandidateRef
exactly.

### Root cause

`DeliveryFinalizer._ensure_branch()` creates every new delivery branch from the symbolic
local branch name in `DeliveryPlan.base_branch`, normally `main`. It does not prove that the
local ref resolves to the CandidateRef base tree, the current verified checkout, or the
observed remote base.

During a multi-ticket run, earlier PRs advanced remote `main`, while the repository's local
`main` stayed at an older merge. WS-07 was correctly based on the already integrated WS-06
tree. Branch creation nevertheless asked Git to transplant the staged candidate onto the
older local `main` tree. Because both trees contained different versions of the same
wayfinder, Git rejected the checkout before the runner could create the delivery commit.

### Evidence

- The gate records the failing command and the wayfinder overwrite refusal.
- WS-07's verified CandidateRef base tree was
  `9716aa9b2d5199dfdbfd5f39a0192cb9220fe2b9`; its candidate tree remained
  `70f936f19e2a34c1448ba544a08a8ed6378cc3d7` at the gate.
- The previous integrated ticket head and observed remote base both had tree
  `9716aa9b2d5199dfdbfd5f39a0192cb9220fe2b9`.
- The local `main` selected by `_ensure_branch()` was commit `185c1e9`, whose tree was
  `5f9675fcce7c4c163f002eab94f5396954e83394`.
- Advancing only the local `main` ref to the already observed remote base made the same
  official delivery transition succeed. The resulting PR head retained the expected
  candidate and was integrated without a semantic revalidation.
- The local-main reflog records the exact `185c1e9` to `ba108b5` recovery transition.

### Hypotheses ruled out

- **Candidate mutation after verification.** Rejected: `git write-tree` remained the exact
  verified candidate tree before recovery.
- **A genuine remote-base semantic conflict.** Rejected: the remote-base tree and current
  checkout tree were identical to the CandidateRef base tree.
- **Ticket-source drift.** Rejected: verification and finalization had completed, and the
  failure occurred before ticket-source finalization.
- **Provider failure.** Rejected: the failure occurred at local Git branch creation before
  any PR mutation.

### Required fix boundary

Delivery branch creation must bind its start point to the verified base identity rather than
trust an arbitrary local branch ref. It must not rewrite the user's local `main`. The runner
must prove the selected start commit has the CandidateRef base tree, preserve the staged
candidate tree, and record the actual base SHA used for delivery lineage. If no safe commit
matches, it must fail closed with a precise reconciliation requirement before Git mutation.

### Regression shape

Use a two-ticket live-shaped fixture: merge the first ticket through the provider so remote
`main` advances while local `main` remains stale; keep the worktree on the first ticket head;
stage a second verified candidate that edits the same file; then deliver it. Assert that the
second branch is created without modifying local `main`, the staged and committed trees remain
exact, replay is idempotent, and true base-tree drift still fails closed.

### Fix

The finalizer now creates a new delivery branch from the current verified checkout only after
proving that checkout's tree equals the CandidateRef base tree. It records that exact start
commit and base tree in delivery metadata and reuses them on replay; older branch receipts can
recover the closest matching first-parent commit. PR lineage uses the actual branch start SHA,
while the provider-facing base branch name is unchanged. A mismatched checkout or contradictory
recorded base fails before branch creation, push, or provider mutation. Local `main` is never
updated or checked out as part of this transition.

### Alternatives ruled out

- Automatically force-updating local `main` mutates user-owned branch state.
- Stashing the candidate breaks CandidateRef identity and adds an unaudited recovery path.
- Ignoring Git's refusal or weakening the staged-tree check could publish a candidate against
  unverified content.
- Treating every occurrence as a human gate leaves AFK runs predictably blocked by normal
  remote progress.

### Confidence: high

The live ledger, tree identities, reflog, source path, and successful one-variable recovery all
identify the same stale-local-ref selection defect.

````
