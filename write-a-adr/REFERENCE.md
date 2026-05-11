# Reference

## ADR Template

<adr-template>

# ADR: <Decision Title>

## Status

Proposed | Accepted | Superseded

## Context

Describe the problem, bug, architectural pressure, or decision point that made this ADR necessary.

Include:

- The user-visible or engineering problem
- The current behavior or architecture
- The constraints that matter
- Relevant evidence from the codebase or current agent context

## Decision

State the chosen architectural decision directly.

This section should be short and unambiguous enough that future contributors can tell whether their changes follow the decision.

## Options Considered

### Option 1: <Name>

- What it would do
- Why it was considered
- Benefits
- Drawbacks

### Option 2: <Name>

- What it would do
- Why it was considered
- Benefits
- Drawbacks

## Consequences

Describe what changes because of the decision.

Include:

- Benefits
- Trade-offs
- Migration or rollout cost
- Operational impact
- Testing impact
- Future constraints this introduces

## Implementation Notes

Give durable guidance for implementing the decision.

Prefer architectural responsibilities, interfaces, invariants, and migration order over line-level instructions. Use file paths only when they are necessary anchors.

## Follow-Up Work

List implementation work that should be tracked in an issue.

</adr-template>

## Issue Template

<issue-template>

# Implement ADR: <Decision Title>

ADR: `docs/adrs/YYYY-MM-DD-<descriptive-slug>.md`

## Problem

Summarize the problem this work addresses and why the ADR decision is needed.

## Scope

Describe the concrete implementation work required.

Include:

- Modules, boundaries, or workflows to change
- Interfaces or contracts to introduce or revise
- Data, migration, or configuration changes
- Observability, operations, or rollout work if relevant

## Acceptance Criteria

- The chosen ADR decision is implemented at the intended boundary.
- Existing behavior covered by the ADR remains compatible unless explicitly changed.
- Relevant tests verify behavior through public boundaries, not implementation details.
- Documentation, configuration, or migration notes are updated where needed.

## Testing Plan

Describe the expected tests:

- Unit, integration, end-to-end, or contract tests to add or update
- Existing tests that should continue to pass
- Manual verification if automation is not practical

## Non-Goals

List work intentionally excluded from this issue.

## Risks and Rollout

Describe migration risks, compatibility concerns, deployment ordering, and rollback considerations.

</issue-template>
