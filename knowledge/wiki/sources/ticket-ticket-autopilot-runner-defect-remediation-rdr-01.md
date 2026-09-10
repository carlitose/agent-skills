---
type: source
title: "Reset stale delivery preparation after candidate invalidation"
identity_key: ticket:ticket-autopilot-runner-defect-remediation/RDR-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-runner-defect-remediation/done/01-reset-stale-delivery-preparation.md
source_digest: sha256:c7d34a2282510ef94e2e0c37b4e8218c7098909e0ae2852a4794e9fb6801c09f
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-01
created_provenance: git-commit
disposition_changed: 2026-09-01
disposition_changed_provenance: git-rename
run_id: runner-defect-remediation-v2-20260901
---

# Reset stale delivery preparation after candidate invalidation

Compiled from `docs/tickets/ticket-autopilot-runner-defect-remediation/done/01-reset-stale-delivery-preparation.md`. Identity is `ticket:ticket-autopilot-runner-defect-remediation/RDR-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-01** via `git-commit`
- Disposition changed: **2026-09-01** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-runner-defect-remediation]]

## Run

Completed under autopilot run `runner-defect-remediation-v2-20260901`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-runner-defect-remediation-rdr-01.md","payload_bytes":3087,"payload_sha256":"c7d34a2282510ef94e2e0c37b4e8218c7098909e0ae2852a4794e9fb6801c09f"}],"payload_bytes":3087,"payload_sha256":"c7d34a2282510ef94e2e0c37b4e8218c7098909e0ae2852a4794e9fb6801c09f","schema":1,"source_digest":"sha256:c7d34a2282510ef94e2e0c37b4e8218c7098909e0ae2852a4794e9fb6801c09f","source_identity":"ticket:ticket-autopilot-runner-defect-remediation/RDR-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3087,"payload_sha256":"c7d34a2282510ef94e2e0c37b4e8218c7098909e0ae2852a4794e9fb6801c09f","schema":1,"source_digest":"sha256:c7d34a2282510ef94e2e0c37b4e8218c7098909e0ae2852a4794e9fb6801c09f","source_identity":"ticket:ticket-autopilot-runner-defect-remediation/RDR-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "RDR-01"
execution_mode: AFK
blocked_by: []
---

# Reset stale delivery preparation after candidate invalidation

## Artifact Graph

- Artifact ID: `artifact:rdr-01-reset-stale-delivery-preparation`
- Role: `ticket`
- Parent: [Ticket Autopilot Runner Defect Remediation](../../specs/ticket-autopilot-runner-defect-remediation.md)

## Parent Spec

[Ticket Autopilot Runner Defect Remediation](../../specs/ticket-autopilot-runner-defect-remediation.md)

## What to Build

Fix GitHub issue [#200](https://github.com/carlitose/agent-skills/issues/200). When a fresh validated CandidateRef supersedes the identity recorded in `delivery.prepared`, invalidate that stale preparation before delivery can reuse it. Preserve branch, commit, push, provider, reconciliation, and history evidence that the reset does not own.

## Acceptance Criteria

- [ ] A focused regression fails on the current baseline by constructing an old prepared CandidateRef, installing and validating a different current candidate, and observing stale preparation reuse or the late prepared-tree contradiction.
- [ ] One kernel-owned transition compares complete CandidateRef fields, archives the incompatible prepared receipt with old/new identity and artifact generation, removes it exactly once, and records a deterministic event.
- [ ] Exact replay is a no-op; an already-current prepared receipt is unchanged.
- [ ] Reset is permitted only before generic preparation can authorize a provider mutation. Existing PR, reconciliation, expected-head, provider, terminal, merge, and source evidence is preserved and contradictions fail closed.
- [ ] The next delivery pass derives and records preparation for the currently validated candidate and cannot reuse the old prepared tree.
- [ ] Candidate invalidation, delivery finalizer, reconciliation, ledger replay, and adjacent exact-identity regressions pass.

## Frontier

Ready. The current `origin/main` contains the late mismatch check but no stale-preparation reset.

## Step-by-Step Implementation Plan

1. Add the failing kernel/finalizer reproduction for an invalidated candidate with stale `delivery.prepared`.
2. Add one narrowly owned reset transition and append-only audit record without clearing unrelated delivery lineage.
3. Invoke it at the last safe boundary before generic delivery preparation is trusted.
4. Prove replay, current-preparation, provider-state, and contradictory-lineage negatives.
5. Run focused and full runner regressions, compile checks, exact diff/tree checks, and Artifact Graph delta.

## Testing Plan

Use pure kernel fixtures for identity and replay plus an isolated Git/fake-provider delivery integration that prepares candidate A, revalidates candidate B, and delivers B. Assert events, artifact generation, exact tree, branch/head behavior, and zero stale provider mutation.

## Out of Scope

- Clearing reconciliation history, provider observations, PR lineage, or terminal proof.
- Weakening the finalizer's exact prepared-tree check.
- Selecting a general delivery-revalidation optimization.

```
