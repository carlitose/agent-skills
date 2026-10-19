---
type: source
title: "PMS-03 — Confirm the multi-session coordination protocol"
identity_key: ticket:pi-multi-session-wayfinder/PMS-03
identity_strength: stable
source_path: docs/tickets/pi-multi-session-wayfinder/03-protocol-decisions.md
source_digest: sha256:b649f1cde7433981d01cb90079b0058aa328bc0811de072cc9674f50151b31dd
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# PMS-03 — Confirm the multi-session coordination protocol

Compiled from `docs/tickets/pi-multi-session-wayfinder/03-protocol-decisions.md`. Identity is `ticket:pi-multi-session-wayfinder/PMS-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-pi-multi-session-wayfinder]]
- Blocked by: [[sources/ticket-pi-multi-session-wayfinder-pms-01]] — `ticket:pi-multi-session-wayfinder/PMS-01`
- Blocked by: [[sources/ticket-pi-multi-session-wayfinder-pms-02]] — `ticket:pi-multi-session-wayfinder/PMS-02`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-pi-multi-session-wayfinder-pms-03.md","payload_bytes":1730,"payload_sha256":"b649f1cde7433981d01cb90079b0058aa328bc0811de072cc9674f50151b31dd"}],"payload_bytes":1730,"payload_sha256":"b649f1cde7433981d01cb90079b0058aa328bc0811de072cc9674f50151b31dd","schema":1,"source_digest":"sha256:b649f1cde7433981d01cb90079b0058aa328bc0811de072cc9674f50151b31dd","source_identity":"ticket:pi-multi-session-wayfinder/PMS-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1730,"payload_sha256":"b649f1cde7433981d01cb90079b0058aa328bc0811de072cc9674f50151b31dd","schema":1,"source_digest":"sha256:b649f1cde7433981d01cb90079b0058aa328bc0811de072cc9674f50151b31dd","source_identity":"ticket:pi-multi-session-wayfinder/PMS-03"} -->
```markdown
---
ticket_schema: 1
ticket_id: "PMS-03"
execution_mode: HITL
blocked_by:
  - "PMS-01"
  - "PMS-02"
---

# PMS-03 — Confirm the multi-session coordination protocol

## Artifact Graph
- Artifact ID: `artifact:pi-multi-session-pms-03`
- Role: `ticket`
- Parent: [pi-multi-session-wayfinder.md](../../specs/pi-multi-session-wayfinder.md)

## Parent Spec
[pi-multi-session-wayfinder.md](../../specs/pi-multi-session-wayfinder.md): Not Yet Specified (third item).

## What to Build
Use [grilling](../../../grilling/SKILL.md) with the human to confirm the protocol, one question at a
time, in plain Italian with concrete examples, starting from the PMS-01 and PMS-02 findings. Decide:
the claim mechanism; who updates the shared map and when; the merge order and conflict handling
when two PRs touch the same files; the message conventions (claim, done, blocked, merged); how a
session picks the next ready ticket. Expected output: a decision spec
`docs/specs/pi-multi-session-protocol.md` created through `to-spec`, linked from the map.

## Acceptance Criteria
- [ ] Every decision above is confirmed by the human, not assumed.
- [ ] The decision spec states the protocol in a few rules a session can follow.
- [ ] The map records the decisions and drops the resolved unknowns.

## Frontier
Done: decisions confirmed and recorded in [pi-multi-session-protocol.md](../../specs/pi-multi-session-protocol.md).

## Step-by-Step Implementation Plan
1. Summarize PMS-01/PMS-02 findings in a few lines.
2. Grill one decision at a time and record each answer.
3. Write the decision spec and update the map.

## Testing Plan
Artifact-graph audit and lint on the changed docs.

## Out of Scope
- Writing the protocol into the skills (PMS-04).

```
