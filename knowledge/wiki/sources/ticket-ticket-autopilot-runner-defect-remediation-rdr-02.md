---
type: source
title: "Prioritize explicit reconciliation over pending merge"
identity_key: ticket:ticket-autopilot-runner-defect-remediation/RDR-02
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-runner-defect-remediation/done/02-prioritize-explicit-reconciliation.md
source_digest: sha256:28fc39338c3964b4080583f8f94a0dc15b4874f635715dd7672168647c197025
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-01
created_provenance: git-commit
disposition_changed: 2026-09-01
disposition_changed_provenance: git-rename
run_id: runner-defect-remediation-v2-20260901
---

# Prioritize explicit reconciliation over pending merge

Compiled from `docs/tickets/ticket-autopilot-runner-defect-remediation/done/02-prioritize-explicit-reconciliation.md`. Identity is `ticket:ticket-autopilot-runner-defect-remediation/RDR-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-01** via `git-commit`
- Disposition changed: **2026-09-01** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-runner-defect-remediation]]

## Run

Completed under autopilot run `runner-defect-remediation-v2-20260901`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-runner-defect-remediation-rdr-02.md","payload_bytes":2999,"payload_sha256":"28fc39338c3964b4080583f8f94a0dc15b4874f635715dd7672168647c197025"}],"payload_bytes":2999,"payload_sha256":"28fc39338c3964b4080583f8f94a0dc15b4874f635715dd7672168647c197025","schema":1,"source_digest":"sha256:28fc39338c3964b4080583f8f94a0dc15b4874f635715dd7672168647c197025","source_identity":"ticket:ticket-autopilot-runner-defect-remediation/RDR-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2999,"payload_sha256":"28fc39338c3964b4080583f8f94a0dc15b4874f635715dd7672168647c197025","schema":1,"source_digest":"sha256:28fc39338c3964b4080583f8f94a0dc15b4874f635715dd7672168647c197025","source_identity":"ticket:ticket-autopilot-runner-defect-remediation/RDR-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "RDR-02"
execution_mode: AFK
blocked_by: []
---

# Prioritize explicit reconciliation over pending merge

## Artifact Graph

- Artifact ID: `artifact:rdr-02-prioritize-explicit-reconciliation`
- Role: `ticket`
- Parent: [Ticket Autopilot Runner Defect Remediation](../../specs/ticket-autopilot-runner-defect-remediation.md)

## Parent Spec

[Ticket Autopilot Runner Defect Remediation](../../specs/ticket-autopilot-runner-defect-remediation.md)

## What to Build

Fix GitHub issue [#201](https://github.com/carlitose/agent-skills/issues/201). In one `resume` call, a validated caller-supplied `reconcile` event for the pending ticket must run before automatic pending-merge dispatch. Recompute merge readiness only after the explicit event persists.

## Acceptance Criteria

- [ ] A focused ordering regression fails on the current baseline with one pending authorized merge plus one explicit reconciliation event and observes the merge path before reconciliation.
- [ ] Resume validates/inspects the exact event batch before using it for priority; malformed, stale, or incomplete events cannot silently suppress pending merge.
- [ ] An explicit reconciliation for the pending ticket executes first and records zero old-head provider merge mutation before the reconciliation result.
- [ ] After event persistence, pending merge eligibility is derived again from current ledger state; a new exact eligible head may proceed, while revalidation-required or gated reconciliation cannot merge the obsolete head.
- [ ] Event batches without the relevant explicit reconciliation preserve current pending-merge ordering and replay semantics.
- [ ] Repository-authorized derived reconciliation, caller events, autonomous merge, provider gates, pause, and crash/replay regressions pass.

## Frontier

Ready. `_resume()` on the current baseline invokes `_drive_pending_merge()` before `_process_events()`.

## Step-by-Step Implementation Plan

1. Add a deterministic fake-provider resume test that records operation order and old-head mutation count.
2. Introduce a bounded validated event-batch inspection or processing seam without a second competing event parser.
3. Process the relevant explicit reconciliation before pending merge and re-derive readiness afterward.
4. Add malformed, unrelated-event, gated, revalidation-required, and replay controls.
5. Run focused/full CLI and reconciliation suites, compilation, exact diff/tree checks, and Artifact Graph delta.

## Testing Plan

Use the public `resume` path with a real event file, fake provider receipts, and a merge mutation spy. Assert ordering, persisted ledger state, expected head, event replay, and no bypass of reconciliation or merge authority.

## Out of Scope

- Giving every explicit event priority over pending merge.
- Manufacturing reconciliation authority or accepting caller semantic-equivalence claims.
- Changing `merge-all` policy except where it delegates to the corrected shared resume ordering.

```
