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
