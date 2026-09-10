---
type: source
title: "Document autopilot dependencies"
identity_key: ticket:autopilot-token-economics/TK-05
identity_strength: stable
source_path: docs/tickets/autopilot-token-economics/done/05-document-autopilot-dependencies.md
source_digest: sha256:8b451f412e4708672df17a32c5b5c883c46255adbc2b67b09e44c066726e92e7
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-11
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
run_id: 7974966ec8d84a35
---

# Document autopilot dependencies

Compiled from `docs/tickets/autopilot-token-economics/done/05-document-autopilot-dependencies.md`. Identity is `ticket:autopilot-token-economics/TK-05`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-11** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-autopilot-token-economics-wayfinder]]

## Run

Completed under autopilot run `7974966ec8d84a35`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-token-economics-tk-05.md","payload_bytes":1854,"payload_sha256":"8b451f412e4708672df17a32c5b5c883c46255adbc2b67b09e44c066726e92e7"}],"payload_bytes":1854,"payload_sha256":"8b451f412e4708672df17a32c5b5c883c46255adbc2b67b09e44c066726e92e7","schema":1,"source_digest":"sha256:8b451f412e4708672df17a32c5b5c883c46255adbc2b67b09e44c066726e92e7","source_identity":"ticket:autopilot-token-economics/TK-05","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1854,"payload_sha256":"8b451f412e4708672df17a32c5b5c883c46255adbc2b67b09e44c066726e92e7","schema":1,"source_digest":"sha256:8b451f412e4708672df17a32c5b5c883c46255adbc2b67b09e44c066726e92e7","source_identity":"ticket:autopilot-token-economics/TK-05"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TK-05"
execution_mode: AFK
blocked_by: []
---

# Document autopilot dependencies

## Artifact Graph

- Artifact ID: `artifact:tk-05-document-autopilot-dependencies`
- Role: `ticket`
- Parent: [Autopilot Token Economics](../../../specs/autopilot-token-economics-wayfinder.md)

## Type
Task

## What to Build
A README section documenting what an autopilot run depends on, so a reader can see the cost
and the coupling before starting a run.

`README.md` already documents Python 3, Git, and the provider CLI under
`## Requirements and command surface`. The missing part is the skill-composition closure:
`ticket-autopilot` composes `execute-ticket`, which composes `code-simplification`,
`code-review`, `qa-test-plan`, and `verification-audit`, with `explain-pr` used by
finalization, plus the loaded references `ticket-envelope-v1`, `delivery-pr-body-v1`,
`merge-critical-path-v1`, and `verification-record`.

## Acceptance Criteria
- [ ] Every skill and reference loaded during a run is listed with its role in the run.
- [ ] The list distinguishes skills the scheduler composes from leaves composed inside
      `execute-ticket`.
- [ ] Existing prerequisite documentation is extended, not duplicated.
- [ ] A test or check fails if the documented closure drifts from the actual composition.

## Frontier
Ready. No dependency and no decision remains.

## Step-by-Step Plan
1. Derive the closure from the current contracts.
2. Add the README section next to the existing requirements material.
3. Add a drift check tying the documented list to the real composition.

## Testing Plan
A static check comparing documented dependencies against the composition declared in the
skills, so the section cannot silently rot.

## Out of Scope
- Publishing token figures, which belongs to `TK-06`.
- Changing the composition itself.

```
