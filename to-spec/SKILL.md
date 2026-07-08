---
name: to-spec
description: Create or update a local spec from existing conversation and codebase context. Use when the user wants a feature spec, decision spec, diagnostic spec, architecture record, bug-analysis spec, or planning document saved under docs/specs.
---

# To Spec

Create or update a spec at `docs/specs/<slug>.md`.

A spec can describe product behavior, a technical decision, an architecture direction,
or a bug diagnosis. Do not restart a full interview by default. First synthesize what
is already known from the conversation, prior agent work, logs, screenshots, prototypes,
or codebase findings. Explore the repository only enough to verify the facts and fill
material gaps.

If the work is too large or foggy to turn into a stable spec in one pass, use
`wayfinder` first to create a persistent map and investigation tickets.

Ask questions only when the answer would materially change the spec. If the user is
still shaping an idea and there is not enough context to proceed, use a short interview
to establish the problem, desired outcome, constraints, and scope.

## Process

### 1. Determine the spec type and target

Classify the work as one of:

- **Feature spec**: a product or workflow change.
- **Decision spec**: a durable technical or architecture choice.
- **Diagnostic spec**: a bug diagnosis, root cause, and recommended fix path.

If the user provided a target spec path, update that file. Otherwise choose a descriptive
kebab-case slug and write to `docs/specs/<slug>.md`. Create `docs/specs` if needed.

If an existing spec clearly covers the same topic, update it instead of creating a
duplicate.

### 2. Reconstruct known context

Start from the current context:

- User-provided goals, bug reports, constraints, logs, screenshots, or design notes.
- Codebase findings already gathered in this session.
- Prior implementation attempts, failed approaches, regressions, or accepted constraints.
- Existing specs, architecture docs, tickets, comments, or commit messages if relevant.

Write a private working summary before exploring:

- The concrete problem or decision pressure.
- The affected users, modules, workflows, or operational constraints.
- The likely solution, decision, or diagnosis.
- What remains uncertain.

### 3. Verify against the repository

Explore enough to avoid writing a speculative spec. Look for:

- Current behavior and nearby implementation patterns.
- Existing architectural boundaries and ownership conventions.
- Tests or workflows that demonstrate the current behavior.
- Callers, data flows, integration points, and failure modes affected by the work.
- Prior specs or docs that constrain the new work.

Keep exploration proportional. The goal is to write a clear spec, not implement the
change.

### 4. Resolve only blocking gaps

If context is sufficient, proceed. If a missing fact would materially change the scope,
decision, or fix path, ask one concise question. In context-first mode, replace broad
interviewing with a short assumptions list and ask only about assumptions that would
change the spec.

### 5. Write the spec

Use the template below. Keep it junior-developer-ready: explain the implementation path,
define unfamiliar terms, make dependencies explicit, and avoid relying on hidden
conversation context.

Skip sections only when they truly do not apply. For decision and diagnostic specs, the
`Decision / Solution` and `Evidence` sections are usually the most important. For feature
specs, `User Stories` and `Implementation Plan` are usually central.

<spec-template>

# <Spec Title>

## Type

Feature spec | Decision spec | Diagnostic spec

## Status

Proposed | Accepted | Superseded

## Problem / Context

Describe the user-visible or engineering problem, current behavior, constraints, and
why this spec exists.

## Goals

- Goal 1
- Goal 2

## Non-Goals

- Work intentionally excluded from this spec.

## Evidence

Include relevant codebase evidence, diagnosis evidence, feedback loops, logs, tests, or
prior findings. Use concrete anchors where useful, but avoid brittle line-level planning.

## Decision / Solution

State the chosen product behavior, architecture direction, or diagnostic conclusion
directly. For a decision spec, include the chosen option and why it fits the constraints.
For a diagnostic spec, include the root cause and recommended fix approach.

## Options Considered

### Option 1: <Name>

- What it would do
- Benefits
- Drawbacks

### Option 2: <Name>

- What it would do
- Benefits
- Drawbacks

## User Stories

For feature specs, list user stories in this format:

1. As an <actor>, I want <feature>, so that <benefit>.

For decision or diagnostic specs, omit this section unless user-facing behavior is central.

## Implementation Plan

Provide a numbered plan in execution order. Each step should explain:

- What to change.
- Why this step comes at this point in the sequence.
- Which module, interface, API contract, schema, workflow, or test surface it affects.
- What to verify before moving to the next step.
- Common pitfalls or assumptions to avoid.

Keep the plan concrete enough to execute, but durable enough that it does not depend on
brittle line numbers or full code snippets.

## Testing Decisions

Describe the testing strategy:

- Public behavior to test.
- Unit, integration, end-to-end, contract, or manual checks to add or update.
- Existing tests or patterns that are relevant.
- What not to test because it would assert implementation details.

## Follow-Up Tickets

List executable work that should become tickets under `docs/tickets/<spec-slug>/`.
If the user asked for tickets now, continue by invoking `to-tickets` after saving the spec.

## Open Questions

- Question or assumption that remains unresolved.

</spec-template>

### 6. Save and report

Write the file to `docs/specs/<slug>.md`, creating the directory if needed. Tell the user
the path and note any assumptions or open questions. Do not paste the full spec unless
the user asks.

