---
type: source
title: "Record the context-passing boundary"
identity_key: ticket:autopilot-token-economics/TK-08
identity_strength: stable
source_path: docs/tickets/autopilot-token-economics/done/08-record-context-passing-boundary.md
source_digest: sha256:fb1dd3ffeda68fd6e81b54a0c73e5328b7416dfa24513a9bc2ad5f794e751ce5
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-11
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
run_id: 7974966ec8d84a35
---

# Record the context-passing boundary

Compiled from `docs/tickets/autopilot-token-economics/done/08-record-context-passing-boundary.md`. Identity is `ticket:autopilot-token-economics/TK-08`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-11** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-autopilot-token-economics-wayfinder]]

## Run

Completed under autopilot run `7974966ec8d84a35`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-token-economics-tk-08.md","payload_bytes":2057,"payload_sha256":"fb1dd3ffeda68fd6e81b54a0c73e5328b7416dfa24513a9bc2ad5f794e751ce5"}],"payload_bytes":2057,"payload_sha256":"fb1dd3ffeda68fd6e81b54a0c73e5328b7416dfa24513a9bc2ad5f794e751ce5","schema":1,"source_digest":"sha256:fb1dd3ffeda68fd6e81b54a0c73e5328b7416dfa24513a9bc2ad5f794e751ce5","source_identity":"ticket:autopilot-token-economics/TK-08","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2057,"payload_sha256":"fb1dd3ffeda68fd6e81b54a0c73e5328b7416dfa24513a9bc2ad5f794e751ce5","schema":1,"source_digest":"sha256:fb1dd3ffeda68fd6e81b54a0c73e5328b7416dfa24513a9bc2ad5f794e751ce5","source_identity":"ticket:autopilot-token-economics/TK-08"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TK-08"
execution_mode: AFK
blocked_by: []
---

# Record the context-passing boundary

## Artifact Graph

- Artifact ID: `artifact:tk-08-record-context-passing-boundary`
- Role: `ticket`
- Parent: [Autopilot Token Economics](../../../specs/autopilot-token-economics-wayfinder.md)

## Type
Task

## What to Build
Make the context-passing boundary observable so it cannot be reopened by guesswork. The
issue asks whether the main agent should use `handoff` to pass context to subagents; the
evidence says no.

`handoff/SKILL.md:12` already states it is neither scheduler state nor a ticket-autopilot
checkpoint, it writes only to the operating-system temporary directory, and it carries
`disable-model-invocation: true`. Context reaches leaves through the `leaf-result` schema-3
contract of `resume --events`, described in `ticket-autopilot/SKILL.md:48-53`. The work is to
state that split explicitly on both sides and test it.

## Acceptance Criteria
- [ ] The `handoff` boundary names the leaf channel it is not, in addition to the scheduler
      state it already excludes.
- [ ] The autopilot side names the channel that does own leaf context passing.
- [ ] A test asserts `handoff` is not referenced as the leaf or subagent context mechanism.
- [ ] No change is made to `handoff` storage, redaction, or expiry behaviour.
- [ ] No change is made to the `leaf-result` schema or its validation.

## Frontier
Ready. The decision is already evidenced in the parent map; only its observability is missing.

## Step-by-Step Plan
1. Add the explicit boundary statement to the `handoff` contract.
2. Name the owning leaf channel on the autopilot side.
3. Add the regression test for the boundary.

## Testing Plan
A prompt-level test asserting the boundary text on both sides and that no skill routes leaf
context through `handoff`.

## Out of Scope
- Changing `leaf-result` schema, validation, or digest rules.
- Repurposing `handoff` as durable or scheduler state.
- Altering redaction, expiry, or temporary-directory behaviour.

```
