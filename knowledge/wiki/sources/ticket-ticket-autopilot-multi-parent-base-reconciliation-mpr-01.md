---
type: source
title: "Support multi-parent PR base reconciliation"
identity_key: ticket:ticket-autopilot-multi-parent-base-reconciliation/MPR-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-multi-parent-base-reconciliation/done/01-support-multi-parent-pr-base-reconciliation.md
source_digest: sha256:7c3aafeb028c56236cd910740051a7f8adcd0bfaefcdfa023d293c01569a54d4
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-29
created_provenance: git-commit
disposition_changed: 2026-08-29
disposition_changed_provenance: git-rename
run_id: mpr-base-reconciliation-20260829
---

# Support multi-parent PR base reconciliation

Compiled from `docs/tickets/ticket-autopilot-multi-parent-base-reconciliation/done/01-support-multi-parent-pr-base-reconciliation.md`. Identity is `ticket:ticket-autopilot-multi-parent-base-reconciliation/MPR-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-29** via `git-commit`
- Disposition changed: **2026-08-29** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-multi-parent-base-reconciliation-diagnostic]]

## Run

Completed under autopilot run `mpr-base-reconciliation-20260829`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-multi-parent-base-reconciliation-mpr-01.md","payload_bytes":3832,"payload_sha256":"7c3aafeb028c56236cd910740051a7f8adcd0bfaefcdfa023d293c01569a54d4"}],"payload_bytes":3832,"payload_sha256":"7c3aafeb028c56236cd910740051a7f8adcd0bfaefcdfa023d293c01569a54d4","schema":1,"source_digest":"sha256:7c3aafeb028c56236cd910740051a7f8adcd0bfaefcdfa023d293c01569a54d4","source_identity":"ticket:ticket-autopilot-multi-parent-base-reconciliation/MPR-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3832,"payload_sha256":"7c3aafeb028c56236cd910740051a7f8adcd0bfaefcdfa023d293c01569a54d4","schema":1,"source_digest":"sha256:7c3aafeb028c56236cd910740051a7f8adcd0bfaefcdfa023d293c01569a54d4","source_identity":"ticket:ticket-autopilot-multi-parent-base-reconciliation/MPR-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "MPR-01"
execution_mode: AFK
blocked_by: []
---

# Support multi-parent PR base reconciliation

## Artifact Graph

- Artifact ID: `artifact:mpr-01-support-multi-parent-pr-base-reconciliation`
- Role: `ticket`
- Parent: [Multi-parent Base Reconciliation Diagnostic](../../specs/ticket-autopilot-multi-parent-base-reconciliation-diagnostic.md)

## Parent Spec

[Multi-parent Base Reconciliation Diagnostic](../../specs/ticket-autopilot-multi-parent-base-reconciliation-diagnostic.md)

## What to Build

Extend the runner's audited reconciliation pipeline to a multi-parent join whose blockers
are integrated and whose recorded delivery base advances after the PR opens. Preserve the
existing single-parent stack behavior and exact-head invariants.

For a multi-parent join, derive the old rebase anchor from
`delivery_lineage.base_sha`, fetch the recorded `base_branch` as the new target, and
reuse the existing durable intent, CandidateRef comparison, bounded semantic revalidation,
Verification Bundle/PR-body rebind, force-with-lease publish, provider readback, and merge
path. Do not select an arbitrary dependency as a Git parent.

## Acceptance Criteria

- [ ] A PR-open multi-parent join with every blocker integrated can reconcile after its
      recorded base branch advances.
- [ ] The old anchor is the ledger's delivery-lineage base SHA and the new target is fetched
      from its recorded base branch; caller-supplied ancestry or semantic claims remain
      forbidden.
- [ ] A clean lineage-only rebase preserves evidence, refreshes the exact head and PR body,
      clears stale one-shot merge state, and can continue through autonomous exact-head
      merge.
- [ ] Semantic tree drift enters the existing bounded revalidation flow and accepts only a
      fresh Verification Bundle bound to the replacement CandidateRef and head.
- [ ] An automatic rebase conflict aborts to the guarded old branch/head, retains durable
      intent, and a later explicitly resolved local head based on the exact target can resume
      without editing the ledger or weakening audit.
- [ ] Any non-integrated blocker rejects reconciliation before Git or provider mutation.
- [ ] Remote-head drift, target drift after provider mutation, and a replay head not based on
      the recorded target continue to fail closed.
- [ ] Existing single-parent stack reconciliation, refresh, bundle-rebind, ledger, and
      forward-test regressions pass.

## Frontier

Ready. The live CR-04/PR #149 state is the motivating reproduction and will consume the fix
after it merges.

## Step-by-Step Implementation Plan

1. Add a failing multi-parent join integration fixture covering base advance and the current
   single-parent-only rejection.
2. Separate reconciliation-target selection from stack classification: retain the current
   parent lineage for a single-parent stack and use delivery base lineage for a join.
3. Require all join blockers to be integrated and record a mode-explicit, Git-derived
   durable intent without accepting caller ancestry.
4. Reuse CandidateRef equivalence/revalidation, refresh, PR-body rebind, guarded publish,
   retarget readback, and autonomous merge.
5. Add conflict-abort/replay and negative lineage tests, then run focused and full runner
   suites plus the workflow forward test.

## Testing Plan

Use local bare Git remotes and the fake provider for deterministic clean, semantic-drift,
conflict/replay, and rejected-lineage scenarios. Run the complete ticket-autopilot unit
suite and forward-test family. Do not use live PR #149 as the sole regression proof.

## Out of Scope

- Automatically resolving semantic merge conflicts.
- Treating dependency-list order as Git ancestry.
- Weakening provider policy, exact-head authorization, or Verification Bundle validation.

```
