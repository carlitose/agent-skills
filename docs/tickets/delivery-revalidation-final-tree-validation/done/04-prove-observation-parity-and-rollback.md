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
