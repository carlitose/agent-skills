---
name: to-tickets
description: Break a spec into independently-grabbable local Markdown ticket files using tracer-bullet vertical slices. Use when the user wants executable tickets, implementation slices, or a ticket folder derived from a spec.
---

# To Tickets

Break a spec into local Markdown tickets using vertical slices, also known as tracer
bullets. Each ticket should be independently grabbable by an implementer and should
describe a narrow, complete path through the system.

Tickets are saved under:

`docs/tickets/<spec-slug>/<NN>-<ticket-slug>.md`

## Process

### 1. Locate the spec

Ask for the spec path only if it is ambiguous. Prefer an explicit path such as
`docs/specs/<slug>.md`. If the spec is not already in context, read it.

### 2. Explore the codebase when needed

If the current context does not already establish the implementation surface, inspect the
repo enough to understand current behavior, nearby patterns, ownership boundaries, and
test conventions. Use the project's domain vocabulary consistently and respect existing
decision specs or architecture docs in the area being changed.

### 3. Draft tracer-bullet slices

Break the spec into thin vertical slices. Each ticket should cut through every layer
needed for one demoable or verifiable behavior, rather than grouping work horizontally by
schema, API, UI, or tests.

Slices may be:

- **AFK**: can be implemented without human interaction.
- **HITL**: requires a human decision, sign-off, design judgment, or external access.

Prefer AFK where possible, but do not hide real gates.

<vertical-slice-rules>
- Each slice delivers a narrow but complete path through the necessary layers.
- A completed slice is demoable or verifiable on its own.
- Prefer many thin slices over few thick ones.
- Blocking edges must be explicit and acyclic.
</vertical-slice-rules>

### 4. Present the breakdown

Before writing files, present the proposed breakdown as a numbered list. For each ticket,
show:

- **Title**: short descriptive name.
- **Type**: AFK or HITL.
- **Blocked by**: ticket numbers or "None".
- **Frontier state**: ready now, blocked by another ticket, or blocked by human input.
- **Spec sections covered**: the source sections or goals this ticket addresses.

Ask only the questions needed to validate granularity and dependencies:

- Does the granularity feel right?
- Are the blocking edges correct?
- Should any tickets be merged or split?
- Are the HITL tickets truly human-gated?

If the user explicitly asked for an AFK/autonomous breakdown, make the best defensible
choices, write them down in the tickets, and continue.

### 5. Create the ticket files

For each approved slice, create a Markdown file at
`docs/tickets/<spec-slug>/<NN>-<ticket-slug>.md`. Number files sequentially in dependency
order so blockers come first. Create directories if needed.

Do not modify the parent spec unless the user explicitly asks.

<ticket-template>

## Parent Spec

[<spec-filename>](../../specs/<spec-filename>)

## What to Build

Describe this vertical slice as end-to-end behavior. Reference specific sections of the
parent spec rather than duplicating the whole spec.

Avoid specific file paths or code snippets unless a contract, state machine, schema, or
type shape encodes a decision more precisely than prose can.

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Blocked By

- None - can start immediately.

Or:

- [<NN>-<ticket-slug>.md](./<NN>-<ticket-slug>.md)

## Frontier

State whether this ticket is ready now, blocked by another ticket, or blocked by human
input. If it is HITL, name the exact decision needed.

## Step-by-Step Implementation Plan

Provide a numbered plan a junior developer can follow. Each step should include:

- What to change.
- Why this step comes at this point in the sequence.
- Which module, interface, API contract, schema, workflow, or test surface it affects.
- What to verify before moving to the next step.
- Common pitfalls or assumptions to avoid.

Keep this concrete enough to execute, but avoid brittle line numbers and overly specific
implementation scaffolding.

## Testing Plan

Describe the tests or checks expected for this ticket, including existing tests that
should keep passing and any manual verification that automation cannot cover.

## Out of Scope

List work intentionally excluded from this ticket.

</ticket-template>

### 6. Report

Tell the user the ticket folder and the paths of all created tickets. Highlight which
tickets are ready now and which are blocked.

