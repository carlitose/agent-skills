---
ticket_schema: 1
ticket_id: "RD-02"
execution_mode: AFK
blocked_by:
  - "RD-01"
---

# Prototype fingerprinted issue escalation

## Artifact Graph

- Artifact ID: `artifact:rd-02-prototype-fingerprinted-issue-escalation`
- Role: `ticket`
- Parent: [Ticket Autopilot Runner-Defect Issue Escalation](../../specs/ticket-autopilot-runner-defect-issue-wayfinder.md)

## Parent Spec

[Ticket Autopilot Runner-Defect Issue Escalation](../../specs/ticket-autopilot-runner-defect-issue-wayfinder.md)

## What to Build

Build a disposable, no-network model for normalized runner-defect eligibility, secret-safe
issue rendering, canonical fingerprints, local outbox receipts, GitHub-search deduplication,
and crash replay. Use the RD-01 report as the ownership and evidence boundary.

## Acceptance Criteria

- [ ] Equivalent failures with different paths, run IDs, timestamps, branches, or stack-line
      numbers produce one fingerprint; materially different owners or failure shapes do not.
- [ ] Project failures, expected gates, provider outages, low-confidence suspicions, and
      unredacted evidence are rejected before any provider operation is proposed.
- [ ] The model represents absent, open-match, closed-match, create-success, ambiguous-match,
      permission-failure, offline, crash-before-create, and lost-response states.
- [ ] Replay after every crash point creates at most one issue and never comments, reopens,
      labels, or closes an existing issue.
- [ ] The prototype exposes a deterministic dry-run transcript and tests proving that ticket,
      gate, verification, and merge state remain unchanged.
- [ ] Keep/discard guidance names the narrow production seam and unresolved RD-03 choices.

## Frontier

Blocked by RD-01. It becomes ready when the research report fixes stable inputs and owners.

## Step-by-Step Implementation Plan

1. Encode the normalized defect record and rejection reasons from RD-01.
2. Compare fingerprint designs and select one with explicit volatility stripping.
3. Model local reservation, provider search, create, readback, and durable receipt phases.
4. Add causal tests and document counterexamples, limits, and production keep/discard advice.

## Testing Plan

Run deterministic unit and state-machine tests with synthetic secret-bearing fixtures that
must be rejected or redacted. Use a fake GitHub adapter only; no network or live issue write.

## Out of Scope

- Production runner integration.
- Deciding or persisting real publication authority.
- General-purpose issue tracker support.
