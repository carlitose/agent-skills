---
type: source
title: "Observe live run token consumption"
identity_key: ticket:autopilot-token-economics/TK-09
identity_strength: stable
source_path: docs/tickets/autopilot-token-economics/09-observe-live-token-consumption.md
source_digest: sha256:57af0881eef781222b742aa293e613850e174bfb9f17467faa0e15196f252e32
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-08-11
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Observe live run token consumption

Compiled from `docs/tickets/autopilot-token-economics/09-observe-live-token-consumption.md`. Identity is `ticket:autopilot-token-economics/TK-09`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-11** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-autopilot-token-economics-wayfinder]]
- Blocked by: [[sources/ticket-autopilot-token-economics-tk-04]] — `ticket:autopilot-token-economics/TK-04`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-token-economics-tk-09.md","payload_bytes":2156,"payload_sha256":"57af0881eef781222b742aa293e613850e174bfb9f17467faa0e15196f252e32"}],"payload_bytes":2156,"payload_sha256":"57af0881eef781222b742aa293e613850e174bfb9f17467faa0e15196f252e32","schema":1,"source_digest":"sha256:57af0881eef781222b742aa293e613850e174bfb9f17467faa0e15196f252e32","source_identity":"ticket:autopilot-token-economics/TK-09","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2156,"payload_sha256":"57af0881eef781222b742aa293e613850e174bfb9f17467faa0e15196f252e32","schema":1,"source_digest":"sha256:57af0881eef781222b742aa293e613850e174bfb9f17467faa0e15196f252e32","source_identity":"ticket:autopilot-token-economics/TK-09"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TK-09"
execution_mode: HITL
blocked_by:
  - "TK-04"
---

# Observe live run token consumption

## Artifact Graph

- Artifact ID: `artifact:tk-09-observe-live-token-consumption`
- Role: `ticket`
- Parent: [Autopilot Token Economics](../../specs/autopilot-token-economics-wayfinder.md)

## Type
Task

## What to Build
One human-run observation of what a real autopilot run consumes, compared against the
worst-case ceiling from `TK-04`, with explicit limitations.

This is a host boundary in the same shape as OI-10. The runner is a Python CLI that never
observes model usage, its ledger budgets `interaction`, `tool-call`, and `wall-time` with no
token axis, and `ticket-autopilot/SKILL.md:34` already reports optional host metrics as
`unavailable` unless configured. Only a user-controlled live session can observe totals, so
this ticket never blocks closing issue #53.

## Acceptance Criteria
- [ ] A user-controlled session runs autopilot on a real ticket and records observed usage.
- [ ] The observation names the host, the ticket, and every condition affecting the total.
- [ ] Observed totals are compared against the `TK-04` ceiling, and any breach is explained.
- [ ] Unobservable quantities are recorded as unavailable rather than estimated.
- [ ] No local or simulated evidence is presented as a live observation.
- [ ] The output recommends whether issue #53 can close and states what remains unobserved.

## Frontier
Blocked by `TK-04` and by human availability. The ceiling must exist first to give the
observation a comparison target.

## Step-by-Step Plan
1. Agree the run scope and the host with the user.
2. Execute the run in a user-controlled session and capture available usage data.
3. Compare against the ceiling and record limitations.
4. Recommend a closure decision for the issue.

## Testing Plan
No automated test. Evidence is the recorded observation with its limitations; a passing local
suite is not proof of live behaviour.

## Out of Scope
- Simulating consumption and reporting it as observed.
- Adding a token axis to ledger budgets or gates.
- Blocking issue closure on this observation.

```
