---
ticket_schema: 1
ticket_id: "RD-03"
execution_mode: HITL
blocked_by:
  - "RD-01"
  - "RD-02"
---

# Freeze issue-publication authority

## Artifact Graph

- Artifact ID: `artifact:rd-03-freeze-issue-publication-authority`
- Role: `ticket`
- Parent: [Ticket Autopilot Runner-Defect Issue Escalation](../../specs/ticket-autopilot-runner-defect-issue-wayfinder.md)

## Parent Spec

[Ticket Autopilot Runner-Defect Issue Escalation](../../specs/ticket-autopilot-runner-defect-issue-wayfinder.md)

## What to Build

Invoke canonical `grilling` and obtain explicit user confirmation of the external publication
contract. Freeze grant scope and lifetime, revocation, minimum diagnosis confidence, allowed
evidence, closed-issue behavior, labels, and failure/retry behavior without changing the
already confirmed destination repository.

## Acceptance Criteria

- [ ] The interview asks one question at a time and distinguishes per-run, repository-scoped,
      and reusable authority with their audit and revocation consequences.
- [ ] The user confirms the minimum diagnosis confidence and evidence required for an
      automatic issue write.
- [ ] Closed matches, ambiguous matches, provider unavailability, lost responses, and grant
      expiry each receive an explicit fail-closed decision.
- [ ] Existing merge, AFK, gate, and provider grants are explicitly rejected as substitutes
      for issue-publication authority.
- [ ] The accepted decision is recorded through `to-spec`, linked from the Wayfinder, and
      narrow enough for RD-04 to implement without guessing.

## Frontier

Blocked by RD-01 and RD-02. Human confirmation is required because the choice authorizes an
external write and materially changes AFK behavior.

## Step-by-Step Implementation Plan

1. Present the research facts and prototype tradeoffs without reopening settled destination.
2. Use `grilling` to resolve grant, claim, lifecycle, and closed-match choices.
3. Restate the complete policy and obtain explicit confirmation.
4. Record the accepted decision spec and update Wayfinder ownership edges.

## Testing Plan

Validate decision completeness against every RD-02 state. No live GitHub mutation occurs in
this ticket; acceptance is the explicit human-confirmed durable decision.

## Out of Scope

- Implementing the chosen contract.
- Creating a real GitHub issue.
- Expanding beyond `carlitose/agent-skills`.
