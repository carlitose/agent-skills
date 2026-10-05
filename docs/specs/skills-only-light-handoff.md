# Short handoff instead of a full Verification Record in skills-only

## Artifact Graph
- Artifact ID: `artifact:skills-only-light-handoff`
- Role: `spec`
- Standalone: true

### Children
- [SLH-01: short skills-only handoff](../tickets/skills-only-light-handoff/01-short-handoff.md)

## Type and Status
Feature/decision spec. Human request, 2026-10-05: the verification trail required in skills-only
is too heavy and gets inflated; simplify it. Builds on SDL-01 (skills-only is the default).

## Current behavior
`execute-ticket` always ends by handing every stage to `verification-audit`, which emits a full
Verification Record (stages, evidence, invariants, boundary delta, gates, claims). The skills-only
contract requires that validated bundle in the handoff and a PR body validated by `explain-pr`.
For ordinary tickets this repeats the same limitations in every section and costs many turns.

## Target behavior
- In skills-only, `execute-ticket` ends with a **short handoff note** with fixed fields: ticket
  (ID, path#sha256), CandidateRef, changed paths, checks (command and outcome, including failed or
  skipped), review (findings or none, inline/not independent), open gates, and claim. Each
  limitation is stated once. The claim is at most implementation-complete; delivered or integrated
  needs provider readback.
- The QA plan in skills-only is the checks list of that note: planned checks with outcomes.
- A full Verification Record through `verification-audit` is required only in the Autopilot lane,
  when the user asks for it, or for a release, live, production, or security claim.
- In skills-only without a full record, the caller writes a short PR body (summary, checks, open
  gates); `explain-pr` and `validate-pr` apply only when a full record exists.

## Invariants
- No claim without evidence: failed, skipped, or not-run checks stay visible, never PASS.
- Required CI on the exact head and provider readback before merge/integration are unchanged.
- The Verification Record contract, validator, and Autopilot lane are unchanged.
- Shared-context review is never called independent.

## Non-goals
- Changing `verification_contract.py`, the record schema, or Autopilot.
- Rewriting historical bundles.

## Verification
Extension unit tests for the injected policy and the skills-only reference; lint; CI.
