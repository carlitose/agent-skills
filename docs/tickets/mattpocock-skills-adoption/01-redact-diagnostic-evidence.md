---
ticket_schema: 1
ticket_id: "U-01"
execution_mode: AFK
blocked_by: []
---

# Redact diagnostic evidence

## Parent Spec
[Open GitHub Issues Remediation](../../specs/open-github-issues-wayfinder.md)

## Adoption Source
[OI-07 approved parity selection](../../research/mattpocock-skills-parity.md#oi-07-approved-adoption-selection)

## What to Build
Add secret-redaction rules to `diagnose` for displayed commands, outputs, and captured artifacts while retaining its single-diagnosis ownership. Touch `triangulate-diagnosis` only if shared handoff wording must point to the same redaction boundary.

## Acceptance Criteria
- [ ] Credentials, tokens, secrets, and secret-bearing command arguments are redacted before display or durable capture.
- [ ] The contract preserves useful non-secret diagnostic evidence and gates when only a redacted artifact can be requested safely.
- [ ] Static fixtures cover representative command, log, and artifact examples without embedding a real secret.

## Frontier
Ready; no dependency or human decision remains.

## Step-by-Step Implementation Plan
1. Inventory the evidence surfaces owned by `diagnose` and define one explicit redaction invariant.
2. Update the skill and only directly shared references without expanding diagnostic orchestration.
3. Add causal static fixtures that fail on unredacted examples and pass on safe placeholders.

## Testing Plan
Run the focused skill-contract tests and repository link/frontmatter checks. Record that no external secret store or live credential was exercised.

## Out of Scope
- Replacing `diagnose` or `triangulate-diagnosis` ownership.
- Collecting, printing, or persisting a live credential.
