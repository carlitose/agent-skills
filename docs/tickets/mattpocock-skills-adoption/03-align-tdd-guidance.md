---
ticket_schema: 1
ticket_id: "U-03"
execution_mode: AFK
blocked_by:
  - "U-02"
---

# Align TDD seam and test guidance

## Parent Spec
[Open GitHub Issues Remediation](../../specs/open-github-issues-wayfinder.md)

## Adoption Source
[OI-07 approved parity selection](../../research/mattpocock-skills-parity.md#oi-07-approved-adoption-selection)

## What to Build
Align `tdd` with pre-agreed seams and the tautological-test anti-pattern, consume the U-02 `codebase-design` vocabulary, and route post-GREEN cleanup to the existing `code-simplification` and review stages. Remove superseded local references only after every inbound link is replaced.

## Acceptance Criteria
- [ ] TDD requires an agreed seam before mocking or opens an explicit gate when the seam is material and unresolved.
- [ ] Guidance rejects tests that merely restate implementation details without causal behavior.
- [ ] Post-GREEN refactoring remains owned by the existing quality stages.
- [ ] Removed references have no remaining inbound links.

## Frontier
Dependency-blocked by U-02.

## Step-by-Step Implementation Plan
1. Map current `tdd` references to the shared U-02 vocabulary.
2. Add seam and tautological-test guidance with one causal RED/GREEN example.
3. Replace inbound links, then remove only demonstrably superseded references.
4. Verify the execute-ticket quality-stage ownership remains unchanged.

## Testing Plan
Run focused TDD/link/static-contract tests plus skill-graph ownership checks.

## Out of Scope
- Reimplementing `code-simplification`, review, or execute-ticket orchestration.
- Deleting a reference that still has an inbound consumer.
