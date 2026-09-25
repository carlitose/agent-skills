---
type: source
title: "JCI-01 — Give fallback judges run-scoped unique identities"
identity_key: ticket:ticket-driver-judge-identity/JCI-01
identity_strength: stable
source_path: docs/tickets/ticket-driver-judge-identity/01-give-fallback-judges-run-scoped-ids.md
source_digest: sha256:851c51253885b1d81a22d7fec482019e7cc4e4d7c54e892b8ae05efe8b7d5d11
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-09-24
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# JCI-01 — Give fallback judges run-scoped unique identities

Compiled from `docs/tickets/ticket-driver-judge-identity/01-give-fallback-judges-run-scoped-ids.md`. Identity is `ticket:ticket-driver-judge-identity/JCI-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-24** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-ticket-driver-judge-identity]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-driver-judge-identity-jci-01.md","payload_bytes":2230,"payload_sha256":"851c51253885b1d81a22d7fec482019e7cc4e4d7c54e892b8ae05efe8b7d5d11"}],"payload_bytes":2230,"payload_sha256":"851c51253885b1d81a22d7fec482019e7cc4e4d7c54e892b8ae05efe8b7d5d11","schema":1,"source_digest":"sha256:851c51253885b1d81a22d7fec482019e7cc4e4d7c54e892b8ae05efe8b7d5d11","source_identity":"ticket:ticket-driver-judge-identity/JCI-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2230,"payload_sha256":"851c51253885b1d81a22d7fec482019e7cc4e4d7c54e892b8ae05efe8b7d5d11","schema":1,"source_digest":"sha256:851c51253885b1d81a22d7fec482019e7cc4e4d7c54e892b8ae05efe8b7d5d11","source_identity":"ticket:ticket-driver-judge-identity/JCI-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "JCI-01"
execution_mode: AFK
blocked_by: []
---

# JCI-01 — Give fallback judges run-scoped unique identities

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-judge-identity-01`
- Role: `ticket`
- Parent: [ticket-driver-judge-identity.md](../../specs/ticket-driver-judge-identity.md)

## Parent Spec
[ticket-driver-judge-identity.md](../../specs/ticket-driver-judge-identity.md)

## What to Build
Allocate the next unused judge name across `Cascade` instances of one run, accounting for existing receipts and partially created session directories. Keep the fresh leaf behavior and fail-closed cascade unchanged.

## Acceptance Criteria
- [ ] Initial semantic gate and another after directed retry can both invoke fallback judges in one run without reusing a name or overwriting existing receipts, with accurate `judge-1`, `judge-2` etc sessions.
- [ ] Existing partially-created session cannot be reused and a second judge may still gate legitimately; Jev question/threshold/answer policy unchanged.
- [ ] Synthetic RED/GREEN, c1b/c2/c3 regression and mandatory quick profile observed, c3b-r4 permanently recorded as a failed attempt.

## Frontier
Ready: observed collision, deterministic reproduction available with fake Jev uncertainty and directed blocker retry. Human benchmark mandate and local fix authorization remain within the c3/c4 goal; no live attempt in this ticket.

## Step-by-Step Implementation Plan
1. Add a fake-leaf causal test forcing uncertainty in two semantic gate passes and verifying distinct judge sessions.
2. Allocate judge identities by existing run receipts and session paths instead of instance-local counter alone; preserve evidence and question behavior.
3. Run RED/GREEN, regression and quick profile; review, deliver/sync exact-head under established repo authority, and separately bind future benchmark starts.

## Testing Plan
Use fake Pi/Jev and temporary repos; test both repeated semantic gate and stale session directory, then full focused suites and selected local profile. No hosted model/Jev.

## Out of Scope
Changing bench38 seed/tests, old receipts, model/Jev policy, customer code, Autopilot runner or forcing uncertain decisions to yes.

```
