---
type: source
title: "Ticket Autopilot Multi-parent Base Reconciliation Diagnostic"
identity_key: artifact:ticket-autopilot-multi-parent-base-reconciliation-diagnostic
identity_strength: stable
source_path: docs/specs/ticket-autopilot-multi-parent-base-reconciliation-diagnostic.md
source_digest: sha256:bde6f621889751dcc49cfffb5b1131dea8ec18e82caefca2f91efa858c5e5bc5
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-08-29
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Ticket Autopilot Multi-parent Base Reconciliation Diagnostic

Compiled from `docs/specs/ticket-autopilot-multi-parent-base-reconciliation-diagnostic.md`. Identity is `artifact:ticket-autopilot-multi-parent-base-reconciliation-diagnostic`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-29** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-ticket-autopilot-multi-parent-base-reconciliation-mpr-01]]
- Child source: [[sources/artifact-ticket-autopilot-parentless-base-reconciliation]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[13],"status":"present"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[12],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/artifact-ticket-autopilot-multi-parent-base-reconciliation-diagnostic.md","payload_bytes":5860,"payload_sha256":"bde6f621889751dcc49cfffb5b1131dea8ec18e82caefca2f91efa858c5e5bc5"}],"payload_bytes":5860,"payload_sha256":"bde6f621889751dcc49cfffb5b1131dea8ec18e82caefca2f91efa858c5e5bc5","schema":1,"source_digest":"sha256:bde6f621889751dcc49cfffb5b1131dea8ec18e82caefca2f91efa858c5e5bc5","source_identity":"artifact:ticket-autopilot-multi-parent-base-reconciliation-diagnostic","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | 13: Non-goals |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | 12: Verification Strategy |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":5860,"payload_sha256":"bde6f621889751dcc49cfffb5b1131dea8ec18e82caefca2f91efa858c5e5bc5","schema":1,"source_digest":"sha256:bde6f621889751dcc49cfffb5b1131dea8ec18e82caefca2f91efa858c5e5bc5","source_identity":"artifact:ticket-autopilot-multi-parent-base-reconciliation-diagnostic"} -->
```markdown
# Ticket Autopilot Multi-parent Base Reconciliation Diagnostic

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-multi-parent-base-reconciliation-diagnostic`
- Role: `spec`
- Standalone: true

### Children

- [Support multi-parent PR base reconciliation](../tickets/ticket-autopilot-multi-parent-base-reconciliation/done/01-support-multi-parent-pr-base-reconciliation.md)
- [Parentless Base Reconciliation](ticket-autopilot-parentless-base-reconciliation.md)

## Diagnosis Report - lens: repro-first

### Root cause

The `resume` handler rejects every `reconcile` event unless the ticket has exactly one
entry in `blocked_by`. That condition correctly identifies the existing stacked-child
path, but it also removes the only audited head-replacement path from a multi-parent join
whose blockers are already integrated and whose ordinary `main` base advances after its PR
opens. The runner therefore cannot use the join's recorded `delivery_lineage.base_sha` as
the old rebase anchor, cannot derive a replacement CandidateRef against the current base, and
cannot refresh the PR body and exact-head merge receipts.

### Evidence

- Live PR #149 is open at head
  `0d15db9ab1801f0d1c27f46012259b06519b7ddd`, targets `main`, and GitHub reports
  `CONFLICTING` / `DIRTY` after `main` advanced to
  `8761f5e4c706cbea6bfc89a32eb72981b031cbe2`.
- Its CR-04 ledger entry has blockers `CR-02`, `CR-03`, and `CR-06`; all three are
  integrated. Delivery lineage records `main` and old base
  `69e333082b798d5d1e376d7136c623371d27541b`.
- Replaying the smallest authoritative event,
  `{"operation":"reconcile","ticket_id":"CR-04"}`, returns
  `TransitionError: only a single-parent stack can be reconciled` before target-base
  fetch or CandidateRef derivation.
- The single-parent implementation already derives Git state, records durable intent,
  aborts a failed automatic rebase safely, accepts a replay head based on the exact recorded
  target, revalidates semantic drift, rebinds the Verification Bundle and PR body, and
  publishes with force-with-lease. The missing decision is how to choose the old anchor for
  a non-stacked join.

### Feedback loop built

The live CR-04 ledger and PR provide a deterministic reproduction: run the runner's
`resume` command with a single `reconcile` event for CR-04 and observe the exact
`TransitionError`. A regression fixture should construct a multi-parent join, integrate
all blockers, open the join PR, advance its recorded base, and prove both the clean-rebase
and conflict/replay paths.

### Fix location and approach

Generalize the reconciliation preparation branch in
`ticket-autopilot/scripts/autopilot/cli.py` without treating a multi-parent join as a
stack. For a join, require every blocker to be integrated, use
`delivery_lineage.base_sha` as the old rebase anchor, fetch the recorded base branch as the
new target, and feed those Git-derived values into the existing intent, CandidateRef,
revalidation, PR-body rebind, guarded publish, and exact-head merge pipeline. Preserve the
current single-parent stacked-child behavior. A semantic conflict remains explicit: abort
the first automatic rebase safely, retain the durable intent, and allow a separately
resolved local head based on the exact target to resume through the same audited path.

### Alternatives ruled out

- GitHub merge policy is not the cause: the runner rejects the event before it asks the
  provider for policy, mergeability, or a merge.
- Missing parent integration is not the cause: all three recorded blockers are integrated.
- Updating the branch manually is not a complete workaround: it changes the provider head
  while the ledger, Verification Bundle, PR body, and merge authorization remain bound to
  the old head.
- Selecting one arbitrary blocker as the parent is invalid: a multi-parent join is not a
  single-parent stack, and dependency order does not prove Git ancestry.

### Confidence: high

The live state reproduces the guard exactly, and the rejected control-flow branch is the
only entry to the runner's audited PR-head replacement machinery.

## Current Behavior

An ordinary multi-parent join may start only after all blockers integrate, but once its PR
is open it has no runner-supported recovery when the recorded base advances. The merge gate
is durable, yet approving it only restores `pr-open`; it does not update the frozen head.

## Target Invariants

- Multi-parent dependency joins remain distinct from stacked single-parent delivery.
- Reconciliation starts only after every blocker is integrated.
- The old anchor comes from immutable delivery lineage, never from dependency ordering or a
  caller-supplied SHA.
- Remote head, local head, target base, CandidateRef, Verification Bundle, PR body, and merge
  authorization remain exact-head bound.
- Semantic equivalence preserves evidence; semantic change starts bounded revalidation.
- Automatic rebase conflicts abort cleanly and retain enough durable intent for audited
  replay after explicit resolution.
- The runner never resolves semantic conflicts by guessing.

## Verification Strategy

- Integration test for a multi-parent join whose base advances without semantic drift.
- Integration test for semantic drift and fresh verification/PR-body bundle rebind.
- Integration test for failed automatic rebase followed by a manually resolved replay head.
- Negative tests for a non-integrated blocker, caller-supplied semantic claims, remote-head
  drift, and a replay head not descended from the exact target.
- Existing single-parent stack, reconciliation refresh, ledger closure, and forward-test
  suites remain green.

## Non-goals

- Automatically choosing content during a semantic merge conflict.
- Weakening force-with-lease, provider readback, or exact-head merge requirements.
- Reclassifying all dependency DAGs as Git stacks.

```
