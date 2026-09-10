---
type: source
title: "Specify the dedicated status-change lane"
identity_key: ticket:lightweight-ticket-status-change/TSC-02
identity_strength: stable
source_path: docs/tickets/lightweight-ticket-status-change/done/02-specify-dedicated-status-change-lane.md
source_digest: sha256:2d6121e530030c2e491cf8fdf2b351c1b797df4a993fd11fc8dfa98cabaee48d
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-31
created_provenance: git-commit
disposition_changed: 2026-09-01
disposition_changed_provenance: git-rename
run_id: lightweight-ticket-status-change-v2-20260831
---

# Specify the dedicated status-change lane

Compiled from `docs/tickets/lightweight-ticket-status-change/done/02-specify-dedicated-status-change-lane.md`. Identity is `ticket:lightweight-ticket-status-change/TSC-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-31** via `git-commit`
- Disposition changed: **2026-09-01** via `git-rename`

## Graph

- Parent source: [[sources/artifact-lightweight-ticket-status-change-wayfinder]]
- Blocked by: [[sources/ticket-lightweight-ticket-status-change-tsc-01]] — `ticket:lightweight-ticket-status-change/TSC-01`

## Run

Completed under autopilot run `lightweight-ticket-status-change-v2-20260831`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-lightweight-ticket-status-change-tsc-02.md","payload_bytes":3592,"payload_sha256":"2d6121e530030c2e491cf8fdf2b351c1b797df4a993fd11fc8dfa98cabaee48d"}],"payload_bytes":3592,"payload_sha256":"2d6121e530030c2e491cf8fdf2b351c1b797df4a993fd11fc8dfa98cabaee48d","schema":1,"source_digest":"sha256:2d6121e530030c2e491cf8fdf2b351c1b797df4a993fd11fc8dfa98cabaee48d","source_identity":"ticket:lightweight-ticket-status-change/TSC-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3592,"payload_sha256":"2d6121e530030c2e491cf8fdf2b351c1b797df4a993fd11fc8dfa98cabaee48d","schema":1,"source_digest":"sha256:2d6121e530030c2e491cf8fdf2b351c1b797df4a993fd11fc8dfa98cabaee48d","source_identity":"ticket:lightweight-ticket-status-change/TSC-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "TSC-02"
execution_mode: AFK
blocked_by:
  - "TSC-01"
---

# Specify the dedicated status-change lane

## Artifact Graph

- Artifact ID: `artifact:tsc-02-dedicated-status-change-lane-specification`
- Role: `ticket`
- Parent: [Lightweight Ticket Status Changes](../../specs/lightweight-ticket-status-change-wayfinder.md)

## Parent Spec

[Lightweight Ticket Status Changes](../../specs/lightweight-ticket-status-change-wayfinder.md)

## What to Build

Using the accepted TSC-01 prototype result, write a focused production specification for the `change-status-ticket` capability and emit independently grabbable tracer-bullet delivery tickets through Ticket Envelope v1. Freeze its routing precedence, lifecycle-only transaction owner, exact inputs and outputs, authority boundaries, tracked/ignored source behavior, crash-safe state ordering, Git/provider delivery, merge separation, and terminal proof without manufacturing an `execute-ticket` quality lifecycle for pure administrative decisions.

## Acceptance Criteria

- [ ] The spec adopts only transaction properties causally proven by TSC-01 and identifies any unresolved gate explicitly.
- [ ] `change-status-ticket` accepts only `open`, `on-hold`, and `canceled` administrative disposition requests and rejects execution lifecycle, readiness, blocked, paused, stopped, and completed changes.
- [ ] Actor, reason, durable authority reference, exact ticket identity, repository identity, and reopen gate inputs fail closed.
- [ ] Routing precedence applies only to explicit administrative-disposition requests; ordinary ticket execution remains on the delivery lane.
- [ ] Tracked-source isolation, exact path allowlist, commit/push/PR readback, independent exact-head merge authority, and fresh terminal proof have one replayable ordering.
- [ ] Ignored-source behavior preserves the external-source boundary and does not silently publish or project tracked completion.
- [ ] Active work, gated/waiting state, missing/retired/ambiguous run ownership, and no-cascade semantics are explicit.
- [ ] Compatibility is opt-in and no existing implementation, publication, wiki, Pi-sync, or cleanup authority is widened.
- [ ] Production tracer-bullet tickets are emitted with deterministic IDs, dependencies, AFK/HITL modes, acceptance criteria, testing plans, and Ticket Envelope v1 front matter.
- [ ] No real ticket status or provider object is changed while specifying the lane.

## Frontier

Blocked by TSC-01. Once its prototype result is accepted, this specification and ticket emission require no live provider action or real disposition authority.

## Step-by-Step Implementation Plan

1. Validate TSC-01's isolation and replay recommendation against the Wayfinder decisions.
2. Freeze the production interface, state machine, authority contract, and failure semantics.
3. Specify tracked and ignored source transaction outcomes and exact readbacks.
4. Define routing and mandatory-workflow integration without a generic docs-only exception.
5. Emit minimal tracer-bullet delivery tickets with explicit dependencies and gates.

## Testing Plan

Lint the specification and emitted Ticket Envelopes, validate Artifact Graph links, and check that no real source path, provider object, authority record, run ledger, or installed skill changed.

## Out of Scope

- Implementing the production capability in this ticket.
- Applying any real status change.
- Revisiting accepted lifecycle vocabulary or no-cascade semantics.
- Inferring disposition, merge, publication, wiki, Pi-sync, or cleanup authority.

```
