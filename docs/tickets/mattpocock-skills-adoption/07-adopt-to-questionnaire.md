---
ticket_schema: 1
ticket_id: "U-07"
execution_mode: AFK
blocked_by: []
---

# Adopt to-questionnaire with a no-send boundary

## Parent Spec
[Open GitHub Issues Remediation](../../specs/open-github-issues-wayfinder.md)

## Adoption Source
[OI-07 approved parity selection](../../research/mattpocock-skills-parity.md#oi-07-approved-adoption-selection)

## What to Build
Add `to-questionnaire` for externalizing a decision the current user cannot answer. Require an explicit intended destination, minimize sensitive context, and render only a draft; sending remains outside the skill.

## Acceptance Criteria
- [ ] The questionnaire identifies the decision owner, destination, context, questions, and response criteria.
- [ ] It follows “grill the send, not the subject” without running a live interview itself.
- [ ] It never sends, posts, emails, or selects a recipient implicitly.
- [ ] Template and metadata tests cover redaction and the no-send boundary.

## Frontier
Ready; no dependency or human decision remains for implementation.

## Step-by-Step Implementation Plan
1. Define the draft questionnaire structure and destination requirement.
2. Add the skill and Codex metadata with sensitive-context minimization.
3. Test output shape and fail-closed behavior when destination is absent.

## Testing Plan
Run template/frontmatter/link tests with fake recipients and no connector or provider calls.

## Out of Scope
- Sending the questionnaire or contacting a third party.
- Replacing live `grilling` ownership.
