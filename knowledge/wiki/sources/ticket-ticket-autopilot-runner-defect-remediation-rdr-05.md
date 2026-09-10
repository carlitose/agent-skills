---
type: source
title: "Unify autonomous readiness for precompleted dependencies"
identity_key: ticket:ticket-autopilot-runner-defect-remediation/RDR-05
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-runner-defect-remediation/done/05-unify-precompleted-autonomous-readiness.md
source_digest: sha256:b7d011b17d9fe623e3be18199f24673c79a6c768cf79e86856dacf7ebfc1e3ab
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-01
created_provenance: git-commit
disposition_changed: 2026-09-02
disposition_changed_provenance: git-rename
run_id: runner-defect-remediation-v2-20260901
---

# Unify autonomous readiness for precompleted dependencies

Compiled from `docs/tickets/ticket-autopilot-runner-defect-remediation/done/05-unify-precompleted-autonomous-readiness.md`. Identity is `ticket:ticket-autopilot-runner-defect-remediation/RDR-05`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-01** via `git-commit`
- Disposition changed: **2026-09-02** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-runner-defect-remediation]]

## Run

Completed under autopilot run `runner-defect-remediation-v2-20260901`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-runner-defect-remediation-rdr-05.md","payload_bytes":3313,"payload_sha256":"b7d011b17d9fe623e3be18199f24673c79a6c768cf79e86856dacf7ebfc1e3ab"}],"payload_bytes":3313,"payload_sha256":"b7d011b17d9fe623e3be18199f24673c79a6c768cf79e86856dacf7ebfc1e3ab","schema":1,"source_digest":"sha256:b7d011b17d9fe623e3be18199f24673c79a6c768cf79e86856dacf7ebfc1e3ab","source_identity":"ticket:ticket-autopilot-runner-defect-remediation/RDR-05","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3313,"payload_sha256":"b7d011b17d9fe623e3be18199f24673c79a6c768cf79e86856dacf7ebfc1e3ab","schema":1,"source_digest":"sha256:b7d011b17d9fe623e3be18199f24673c79a6c768cf79e86856dacf7ebfc1e3ab","source_identity":"ticket:ticket-autopilot-runner-defect-remediation/RDR-05"} -->
```markdown
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

```
