---
ticket_schema: 1
ticket_id: "RD-01"
execution_mode: AFK
blocked_by: []
---

# Map runner-defect evidence and escalation seams

## Artifact Graph

- Artifact ID: `artifact:rd-01-map-runner-defect-escalation-seams`
- Role: `ticket`
- Parent: [Ticket Autopilot Runner-Defect Issue Escalation](../../specs/ticket-autopilot-runner-defect-issue-wayfinder.md)

## Parent Spec

[Ticket Autopilot Runner-Defect Issue Escalation](../../specs/ticket-autopilot-runner-defect-issue-wayfinder.md)

## What to Build

Produce a source-backed update to the owning Wayfinder that traces how runner-owned defects
are currently detected, diagnosed, gated, persisted, and exposed through provider adapters.
Separate observed code and contracts from proposed issue-escalation policy. Define the
smallest secret-safe evidence shape that RD-02 can model without calling GitHub.

## Acceptance Criteria

- [ ] The report identifies exact owners for exception classification, gate creation,
      diagnostic output, ledger history, provider capabilities, and external mutation guards.
- [ ] It distinguishes runner defects from project failures, provider/environment failures,
      expected gates, unsupported configurations, and user errors with counterexamples.
- [ ] The report defines a proposed normalized defect record and lists every field excluded
      by the diagnostic secret-redaction boundary.
- [ ] It maps deduplication, crash, replay, permission, offline, and pre-ledger failure cases
      without claiming an implementation exists.
- [ ] It identifies the safest integration seam and the tests needed to prove that issue
      escalation cannot alter ticket, gate, verification, or merge state.
- [ ] The Wayfinder records the resulting evidence, decisions, remaining unknowns, and exact
      RD-02 input contract. Any separate managed output is created only with reciprocal graph
      links in the same candidate.

## Frontier

Ready. Repository scope and destination are fixed; current runner ownership is the missing
input for RD-02.

## Step-by-Step Implementation Plan

1. Trace runner exceptions, gates, ledger transitions, provider negotiation, and diagnostics.
2. Classify observed failure families and identify stable versus volatile evidence.
3. Model lifecycle and crash boundaries for create, dedupe, retry, and unavailable provider.
4. Fold the source-backed findings and resulting RD-02 contract into the Wayfinder.

## Testing Plan

Use read-only source inspection and focused existing tests. Validate the updated Wayfinder and
Artifact Graph. No GitHub issue mutation, credential probe, or raw ledger capture is allowed.

## Out of Scope

- Implementing issue creation or a provider command.
- Choosing publication authority or closed-issue behavior.
- Diagnosing project bugs unrelated to the runner.
