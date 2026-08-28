---
ticket_schema: 1
ticket_id: "RD-05"
execution_mode: HITL
blocked_by:
  - "RD-04"
---

# Forward-test live GitHub issue idempotency

## Artifact Graph

- Artifact ID: `artifact:rd-05-forward-test-live-github-issue-idempotency`
- Role: `ticket`
- Parent: [Ticket Autopilot Runner-Defect Issue Escalation](../../specs/ticket-autopilot-runner-defect-issue-wayfinder.md)

## Parent Spec

[Ticket Autopilot Runner-Defect Issue Escalation](../../specs/ticket-autopilot-runner-defect-issue-wayfinder.md)

## What to Build

With explicit live-boundary authorization, run one controlled synthetic runner-defect
escalation against `carlitose/agent-skills`, verify the created or deduplicated issue and
receipt, then replay the same fingerprint to prove no second external mutation occurs.

## Acceptance Criteria

- [ ] The user authorizes the exact repository, sanitized issue preview, and test fingerprint
      before the first provider mutation.
- [ ] Live readback binds issue number, URL, body hash, fingerprint marker, repository, and
      provider identity to the durable receipt.
- [ ] Replaying the exact defect observes the same issue and performs no second create,
      comment, reopen, close, label, or assignment mutation.
- [ ] Permission denial, ambiguous search, and unavailable API behavior remain separately
      gated or explicitly unobserved; local fakes cannot upgrade those live claims.
- [ ] The test issue receives the user-confirmed cleanup recommendation; cleanup itself is
      not performed without separate authorization.
- [ ] The Wayfinder records live evidence, residual limits, and whether the destination is
      reached or another bounded ticket is required.

## Frontier

Blocked by RD-04 and by explicit human authorization for the exact live GitHub mutation.

## Step-by-Step Implementation Plan

1. Render and validate the synthetic sanitized issue preview and exact fingerprint.
2. Obtain explicit live-boundary authorization and execute one create-or-dedupe attempt.
3. Read back the provider issue and validate the durable receipt.
4. Replay the same input, prove no second mutation, and record limitations and cleanup advice.

## Testing Plan

Run the production dry-run first, then one authorized live provider scenario and an exact
replay. Capture only sanitized status, IDs, hashes, and URLs; never credentials or headers.

## Out of Scope

- Testing with a real private bug or raw production ledger.
- Closing or deleting the test issue without separate authorization.
- Claiming non-GitHub provider support.
