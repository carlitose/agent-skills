---
type: source
title: "Audit model-invocation exposure"
identity_key: ticket:autopilot-token-economics/TK-07
identity_strength: stable
source_path: docs/tickets/autopilot-token-economics/done/07-audit-model-invocation-exposure.md
source_digest: sha256:b7a151cd58a266815fb17110a66ec90f6607ad8855b56dff167406b392525d7a
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-11
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
run_id: 7974966ec8d84a35
---

# Audit model-invocation exposure

Compiled from `docs/tickets/autopilot-token-economics/done/07-audit-model-invocation-exposure.md`. Identity is `ticket:autopilot-token-economics/TK-07`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-11** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-autopilot-token-economics-wayfinder]]

## Run

Completed under autopilot run `7974966ec8d84a35`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-token-economics-tk-07.md","payload_bytes":2064,"payload_sha256":"b7a151cd58a266815fb17110a66ec90f6607ad8855b56dff167406b392525d7a"}],"payload_bytes":2064,"payload_sha256":"b7a151cd58a266815fb17110a66ec90f6607ad8855b56dff167406b392525d7a","schema":1,"source_digest":"sha256:b7a151cd58a266815fb17110a66ec90f6607ad8855b56dff167406b392525d7a","source_identity":"ticket:autopilot-token-economics/TK-07","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2064,"payload_sha256":"b7a151cd58a266815fb17110a66ec90f6607ad8855b56dff167406b392525d7a","schema":1,"source_digest":"sha256:b7a151cd58a266815fb17110a66ec90f6607ad8855b56dff167406b392525d7a","source_identity":"ticket:autopilot-token-economics/TK-07"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TK-07"
execution_mode: AFK
blocked_by: []
---

# Audit model-invocation exposure

## Artifact Graph

- Artifact ID: `artifact:tk-07-audit-model-invocation-exposure`
- Role: `ticket`
- Parent: [Autopilot Token Economics](../../../specs/autopilot-token-economics-wayfinder.md)

## Type
Task

## What to Build
A stated criterion for when a skill should be hidden from the model-visible listing with
`disable-model-invocation: true`, the flag applied where the criterion says it belongs, and a
check that keeps the listing from drifting.

The flag demonstrably works: `grill-me`, `grill-with-docs`, `handoff`,
`resolving-merge-conflicts`, `to-questionnaire`, and `wizard` carry it and are absent from an
observed model-visible listing, accounting for 267 words already saved. The lever is real but
small, so the criterion matters more than the raw saving.

## Acceptance Criteria
- [ ] The criterion is written down and distinguishes user-invoked-only workflows from skills
      the model must be able to select autonomously.
- [ ] Every skill is classified against the criterion, with the reason recorded.
- [ ] Skills that must stay model-invocable are not hidden merely to reduce the listing.
- [ ] Oversized descriptions are reported rather than silently rewritten.
- [ ] A check fails when a new skill is added without a classification.
- [ ] Uninstalled skills are noted as costing nothing today, without prescribing installation.

## Frontier
Ready. No dependency and no decision remains.

## Step-by-Step Plan
1. Write the hiding criterion.
2. Classify every skill and record each reason.
3. Apply flags only where the criterion requires it.
4. Add the drift check for newly added skills.

## Testing Plan
A static check over skill front matter asserting every skill carries a classification and
that hidden skills match the criterion.

## Out of Scope
- Hiding skills that the model legitimately needs to select.
- Rewriting descriptions for length alone.
- Installing skills that are currently absent from the install root.

```
