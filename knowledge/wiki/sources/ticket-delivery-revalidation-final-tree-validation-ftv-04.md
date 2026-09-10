---
type: source
title: "Prove Observation Parity and Safe Rollback"
identity_key: ticket:delivery-revalidation-final-tree-validation/FTV-04
identity_strength: stable
source_path: docs/tickets/delivery-revalidation-final-tree-validation/done/04-prove-observation-parity-and-rollback.md
source_digest: sha256:df17c7e3e335e69a943a8e1cd5c140175f177066ecc6188b810e605083a55b57
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-02
created_provenance: git-commit
disposition_changed: 2026-09-03
disposition_changed_provenance: git-rename
run_id: delivery-revalidation-final-tree-validation-ftv04-corrective-v2-20260903
---

# Prove Observation Parity and Safe Rollback

Compiled from `docs/tickets/delivery-revalidation-final-tree-validation/done/04-prove-observation-parity-and-rollback.md`. Identity is `ticket:delivery-revalidation-final-tree-validation/FTV-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-02** via `git-commit`
- Disposition changed: **2026-09-03** via `git-rename`

## Graph

- Parent source: [[sources/artifact-delivery-revalidation-final-tree-validation-decision]]
- Blocked by: [[sources/ticket-delivery-revalidation-final-tree-validation-ftv-03]] — `ticket:delivery-revalidation-final-tree-validation/FTV-03`

## Run

Completed under autopilot run `delivery-revalidation-final-tree-validation-ftv04-corrective-v2-20260903`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-delivery-revalidation-final-tree-validation-ftv-04.md","payload_bytes":3987,"payload_sha256":"df17c7e3e335e69a943a8e1cd5c140175f177066ecc6188b810e605083a55b57"}],"payload_bytes":3987,"payload_sha256":"df17c7e3e335e69a943a8e1cd5c140175f177066ecc6188b810e605083a55b57","schema":1,"source_digest":"sha256:df17c7e3e335e69a943a8e1cd5c140175f177066ecc6188b810e605083a55b57","source_identity":"ticket:delivery-revalidation-final-tree-validation/FTV-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3987,"payload_sha256":"df17c7e3e335e69a943a8e1cd5c140175f177066ecc6188b810e605083a55b57","schema":1,"source_digest":"sha256:df17c7e3e335e69a943a8e1cd5c140175f177066ecc6188b810e605083a55b57","source_identity":"ticket:delivery-revalidation-final-tree-validation/FTV-04"} -->
```markdown
---
ticket_schema: 1
ticket_id: "FTV-04"
execution_mode: AFK
blocked_by:
  - "FTV-03"
---

# Prove Observation Parity and Safe Rollback

## Artifact Graph

- Artifact ID: `artifact:delivery-revalidation-observation-parity`
- Role: `ticket`
- Parent: [Final-Tree Validation Architecture Decision](../../specs/delivery-revalidation-final-tree-validation-decision.md)

## Parent Spec

[Final-Tree Validation Architecture Decision](../../specs/delivery-revalidation-final-tree-validation-decision.md)

## What to Build

Run and retain the controlled observation evidence required by the rollout contract. Exercise one
ordinary tracked delivery through the unchanged authoritative path while observation mode computes
the prospective pre-quality lane. Compare the complete manifest, exact `D`, receipt, link closure,
final Verification Record, rendered body binding, provider-head lineage, and terminal proof.

Run the frozen positive, fallback, blocked, crash, replay, historical, and authority-separation
matrix against the production implementation. Prove that switching new runs to `off` restores the
current full process and that an already persisted intent continues exact version-bound replay or
blocks. Preserve content-addressed run artifacts and a concise checked-in result summary without
claiming wall-time, token, or live-provider savings.

## Acceptance Criteria

- [ ] A controlled ordinary tracked observation and authoritative delivery produce identical `D`,
      manifest effects, receipt, link closure, final Verification Record, rendered CandidateRef,
      and terminal lineage.
- [ ] Every DRV-02 outcome class remains correct against production code: one narrow-positive,
      recoverable checkpoints, exact replay, full-path fallbacks, and fail-closed blockers.
- [ ] Mutation coverage proves that one extra path/blob/mode/receipt/link/reconciliation/provider or
      stale-identity change cannot pass the classifier or parity check.
- [ ] Historical ledgers without the manifest replay literally through the current full path.
- [ ] Mode `off` keeps new runs on current behavior, while an in-flight durable intent replays under
      its recorded contract version and never disappears.
- [ ] Evidence reports command/check labels only as logical counts and makes no wall-time, token,
      provider, or universal performance claim.
- [ ] Fake-provider or disposable evidence is labeled simulated and grants no live-provider or
      merge authority.
- [ ] The completion handoff records exact content-addressed paths and hashes for the controlled
      observation, matrix, rollback, and static/full-suite results.

## Frontier

Dependency-blocked by `FTV-03`.

## Step-by-Step Implementation Plan

1. Build one deterministic forward harness over the production observer and enabled lane in
   disposable repositories.
2. Execute the controlled observation-to-authoritative parity trace and capture exact identities.
3. Execute all positive, fallback, blocker, crash, replay, historical, and adjacent-authority
   matrices, including mode rollback with an in-flight intent.
4. Store content-addressed run evidence and add a concise tracked result summary bound to this
   ticket and the decision spec.
5. Run focused and broad regression suites and preserve failures literally rather than normalizing
   them into a parity pass.

## Testing Plan

- The controlled system trace is the primary acceptance test.
- Deterministic rerun must produce byte-identical normalized evidence apart from explicitly
  excluded timestamps or scratch paths.
- Existing ticket-autopilot and extension suites protect scheduler and routing behavior.
- Static compilation, diff checks, exact final-tree identity, and Artifact Graph checks cover the
  tracked summary.

## Out of Scope

- Changing the default to `enabled`.
- Live provider mutation.
- Treating one controlled trace as a general performance benchmark.
- Repairing unrelated baseline warnings or context-budget failures.

```
