---
type: source
title: "Consume all resolved reconciliation gates"
identity_key: ticket:ticket-autopilot-runner-defect-remediation/RDR-03
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-runner-defect-remediation/done/03-consume-reconciliation-gates.md
source_digest: sha256:7b6b7566f3915dfacbb7a7fe3be2df5b34783c7d900d1363e6f773a306a66e4c
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-01
created_provenance: git-commit
disposition_changed: 2026-09-02
disposition_changed_provenance: git-rename
run_id: runner-defect-remediation-v2-20260901
---

# Consume all resolved reconciliation gates

Compiled from `docs/tickets/ticket-autopilot-runner-defect-remediation/done/03-consume-reconciliation-gates.md`. Identity is `ticket:ticket-autopilot-runner-defect-remediation/RDR-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-01** via `git-commit`
- Disposition changed: **2026-09-02** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-runner-defect-remediation]]

## Run

Completed under autopilot run `runner-defect-remediation-v2-20260901`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-runner-defect-remediation-rdr-03.md","payload_bytes":3019,"payload_sha256":"7b6b7566f3915dfacbb7a7fe3be2df5b34783c7d900d1363e6f773a306a66e4c"}],"payload_bytes":3019,"payload_sha256":"7b6b7566f3915dfacbb7a7fe3be2df5b34783c7d900d1363e6f773a306a66e4c","schema":1,"source_digest":"sha256:7b6b7566f3915dfacbb7a7fe3be2df5b34783c7d900d1363e6f773a306a66e4c","source_identity":"ticket:ticket-autopilot-runner-defect-remediation/RDR-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3019,"payload_sha256":"7b6b7566f3915dfacbb7a7fe3be2df5b34783c7d900d1363e6f773a306a66e4c","schema":1,"source_digest":"sha256:7b6b7566f3915dfacbb7a7fe3be2df5b34783c7d900d1363e6f773a306a66e4c","source_identity":"ticket:ticket-autopilot-runner-defect-remediation/RDR-03"} -->
```markdown
---
ticket_schema: 1
ticket_id: "RDR-03"
execution_mode: AFK
blocked_by: []
---

# Consume all resolved reconciliation gates

## Artifact Graph

- Artifact ID: `artifact:rdr-03-consume-reconciliation-gates`
- Role: `ticket`
- Parent: [Ticket Autopilot Runner Defect Remediation](../../specs/ticket-autopilot-runner-defect-remediation.md)

## Parent Spec

[Ticket Autopilot Runner Defect Remediation](../../specs/ticket-autopilot-runner-defect-remediation.md)

## What to Build

Fix GitHub issue [#202](https://github.com/carlitose/agent-skills/issues/202). A successful Git-derived reconciliation must consume every open gate on that ticket that represents the resolved reconciliation condition—`provider-merge`, `stack-reconciliation`, and `stack-reconciliation-recovery`—while preserving unrelated gates.

## Acceptance Criteria

- [ ] A focused regression fails on the current baseline by completing ordinary reconciliation with both provider-merge and stack-reconciliation gates open and observing a residual open stack gate.
- [ ] One canonical selector defines the exact reconciliation-condition gate categories and is reused by ordinary, proposal-backed, and recovery paths.
- [ ] The exact selected gate IDs are passed and consumed with explicit scheduler/proposal evidence in the same persisted reconciliation transition; a failed preparation cannot leave a partial durable closure.
- [ ] Successful equivalent and revalidation-required preparation close the resolved old-head condition before advancing; exact replay returns the same closed set.
- [ ] Human/start, source, provider-environment, resource-budget, verification, publication, wiki, Pi, and unrelated ticket/run gates remain unchanged.
- [ ] Ledger history records which gate IDs were consumed and validates replay literally.
- [ ] Reconciliation, proposal recovery, gate, ledger, autonomous merge, and terminal-boundary regressions pass.

## Frontier

Ready. The current `_merge_gate_ids()` selects only `provider-merge`; other reconciliation paths maintain separate category lists.

## Step-by-Step Implementation Plan

1. Add ordinary and proposal-backed failing fixtures with mixed relevant/unrelated gate sets.
2. Centralize reconciliation-condition gate selection without broad category matching.
3. Bind gate consumption to the successful reconciliation state transition and append exact IDs/evidence.
4. Prove rollback on preparation failure, idempotent replay, and unrelated-gate preservation.
5. Run focused/full kernel, ledger, CLI, reconciliation, and terminal suites plus compilation and graph checks.

## Testing Plan

Use kernel transaction fixtures and public resume integration with fake provider/Git state. Assert gate states, event order, consumed IDs, rollback, ticket state, merge readiness, and replay-derived run state.

## Out of Scope

- Auto-approving any human or authority gate.
- Closing provider/environment gates whose condition was not resolved by reconciliation.
- Rewriting historical gate events or reasons.

```
