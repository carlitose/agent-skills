---
ticket_schema: 1
ticket_id: "RDR-05"
execution_mode: AFK
blocked_by: []
---

# Unify autonomous readiness for precompleted dependencies

## Artifact Graph

- Artifact ID: `artifact:rdr-05-unify-precompleted-autonomous-readiness`
- Role: `ticket`
- Parent: [Ticket Autopilot Runner Defect Remediation](../../specs/ticket-autopilot-runner-defect-remediation.md)

## Parent Spec

[Ticket Autopilot Runner Defect Remediation](../../specs/ticket-autopilot-runner-defect-remediation.md)

## What to Build

Fix GitHub issue [#205](https://github.com/carlitose/agent-skills/issues/205), the precompleted-parent-without-lineage defect previously excluded by PCR-01 and TIP-01. Kernel scheduling and ledger replay must use one pure autonomous dependency-readiness rule, including the exact compatibility shape for a dependency already completed at snapshot time.

## Acceptance Criteria

- [ ] Extend the existing precompleted-dependency fixture so the child reaches `pr-open`, receives autonomous merge authorization, becomes the pending runner merge, and fails on the current baseline when ledger validation derives an incompatible run state.
- [ ] One shared pure predicate is used by `Kernel.autonomous_merge_dependencies_ready()` and `AtomicLedger._derived_run_state()`; neither retains a divergent local approximation.
- [ ] The predicate accepts a single parent without delivery lineage only when the parent is `state=integrated`, `disposition=completed`, and `candidate_ref=null`.
- [ ] Missing child lineage is tolerated only for that exact precompleted compatibility branch; ordinary single-parent stacks still require matching lineage dictionaries/base branches.
- [ ] No-blocker and integrated multi-parent semantics remain unchanged.
- [ ] Near misses—open/held/canceled disposition, non-integrated state, non-null candidate, malformed lineage, base mismatch, or missing ordinary lineage—remain not ready and replay-valid.
- [ ] Full save/load/history replay derives the same `running`/`waiting` state as the kernel for every matrix row, and the exact autonomous child can continue to expected-head provider merge and terminal proof in integration coverage.

## Frontier

Ready. PCR-01 and TIP-01 explicitly name this defect as separate/out of scope, and no existing executable ticket owns it.

## Step-by-Step Implementation Plan

1. Turn the current kernel-only precompleted test into a failing kernel/ledger transition and replay feedback loop.
2. Extract one dependency-readiness helper in a non-circular shared owner.
3. Replace both runtime and ledger-derived implementations with the helper.
4. Add the complete accepted/rejected topology matrix and one autonomous merge integration path.
5. Run focused/full kernel, ledger, CLI, merge, terminal, compilation, exact diff/tree, and graph checks.

## Testing Plan

Use Ticket Envelope fixtures with a `done/` dependency, direct ledger save/load/history validation, and a fake GitHub provider for exact-head merge. Assert predicate parity, pending merge identity, run state, provider mutation count, and terminal integration.

## Out of Scope

- Synthesizing CandidateRef or delivery lineage for historical precompleted tickets.
- Accepting generic completed parents with missing evidence.
- Redesigning lifecycle initialization or terminal proof.
