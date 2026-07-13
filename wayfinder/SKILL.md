---
name: wayfinder
description: Plan huge, foggy, or multi-session work by maintaining a local wayfinding spec and investigation tickets under docs/specs and docs/tickets. Use when one agent session cannot hold the destination, unknowns, decisions, and execution frontier, or when work must be mapped before normal spec-to-ticket execution.
---

# Wayfinder

Create a persistent local map for work that is too large, vague, or multi-stage to hold
in one agent session. Wayfinder plans by default. Do not execute the final destination
unless the user explicitly asks.

Wayfinder is local-file-first:

- Maps live under `docs/specs/<slug>.md` or `docs/specs/<slug>-wayfinder.md`.
- Tickets live under `docs/tickets/<spec-slug>/`.
- No hosted tracker is required.
- Durable decisions are recorded as decision specs or diagnostic specs.

## Inputs

Accept any of:

- A loose goal.
- A partial spec.
- A failing project direction with many unknowns.
- A ticket folder that no longer has a clear frontier.
- Prior notes, logs, branches, prototypes, or conversation context.

Ask one concise question only when the destination itself is ambiguous. Otherwise create
or update the map with explicit assumptions.

## Process

### 1. Choose the map and slug

If the user provided a path, use it. Otherwise choose a kebab-case slug.

- Use `docs/specs/<slug>.md` when the map is the main planning spec.
- Use `docs/specs/<slug>-wayfinder.md` when there is already, or will likely be, a main
  feature, decision, or diagnostic spec with the same slug.

Derive `<spec-slug>` from the map filename stem. If maintaining `<slug>-wayfinder.md`
beside `<slug>.md`, use `<slug>` for the ticket folder so destination tickets stay
together.

### 2. Reconstruct the current map

Read existing specs, tickets, notes, and code only as needed to understand:

- The destination.
- What is already decided.
- What remains unspecified.
- What is explicitly out of scope.
- The frontier: the next blocking edge, unknown, or dependency.

Keep this bounded. The output is a map and tickets, not a full implementation.

### 3. Write or update the wayfinding spec

Use this structure:

```markdown
# <Title>

## Type

Wayfinding spec

## Status

Active

## Destination

The outcome this map is trying to make reachable.

## Decisions So Far

- Decision, evidence, and where it is recorded.

## Not Yet Specified

- Unknowns that must become clear before reliable execution.

## Out of Scope

- Work this map intentionally excludes.

## Frontier / Blocking Edges

- Edge: why it blocks progress, what would unblock it, and which ticket owns it.

## Ticket Plan

- Ticket number, type, title, and expected output.

## Next Review

- What the next agent or human should inspect after tickets complete.
```

For durable architecture, product, or diagnosis decisions, create or update a normal
decision spec or diagnostic spec with `to-spec`, then link it from `Decisions So Far`.

### 4. Create investigation tickets

Create tickets under `docs/tickets/<spec-slug>/` in dependency order. Use file names like
`01-research-auth-boundary.md` or `02-prototype-parser-contract.md`.

Ticket types:

These are ticket labels, not local skill names. Use them to classify the next piece of
uncertainty or execution work inside the ticket file.

- **research**: answer a factual, codebase, product, or external-documentation question
  with cited evidence.
- **prototype**: build a disposable or reversible proof that reduces uncertainty.
- **grilling**: get human decisions by asking sharp questions and recording answers or
  assumptions.
- **task**: execute a concrete build, docs, migration, or cleanup step.

Each ticket should include:

```markdown
## Parent Spec

[<spec-filename>](../../specs/<spec-filename>)

## Type

research | prototype | grilling | task

## Outcome

The specific question answered, decision enabled, or behavior delivered.

## Acceptance Criteria

- [ ] The output is saved or summarized where the parent spec expects it.
- [ ] Evidence, decisions, and remaining uncertainty are explicit.

## Blocked By

- None - can start immediately.

## Frontier

Why this ticket is the next edge to cross, or what blocks it.

## Work Plan

1. Concrete step.
2. Concrete step.

## Evidence to Capture

- Files, commands, sources, screenshots, or user answers needed by the map.

## Out of Scope

- Work intentionally excluded from this ticket.
```

### 5. Stop at the plan

By default, report the map path, ticket folder, ready tickets, blocked tickets, and the
recommended next step. Do not start `execute-ticket` or `ticket-autopilot` unless the
user explicitly asks you to execute.

When the user does ask to execute, route ready tickets through `execute-ticket` one at a
time, or through `ticket-autopilot` / `super-autopilote-ticket` for a folder-level loop.

## Maintenance Rules

- After a ticket completes, fold its evidence and decisions back into the map.
- Move obsolete unknowns out of `Not Yet Specified` rather than leaving stale questions.
- Keep the frontier small: the next few blocking edges, not every possible future task.
- Prefer another investigation ticket over guessing when the path is still foggy.
- Keep final build tickets narrow enough for `execute-ticket`.