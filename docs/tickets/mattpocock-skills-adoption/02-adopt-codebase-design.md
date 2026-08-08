---
ticket_schema: 1
ticket_id: "U-02"
execution_mode: AFK
blocked_by: []
---

# Adopt the shared codebase-design reference

## Parent Spec
[Open GitHub Issues Remediation](../../specs/open-github-issues-wayfinder.md)

## Adoption Source
[OI-07 approved parity selection](../../research/mattpocock-skills-parity.md#oi-07-approved-adoption-selection)

## What to Build
Add `codebase-design` as the single shared vocabulary owner for modules, interfaces, depth, seams, and adapters. Package `SKILL.md`, `DEEPENING.md`, `DESIGN-IT-TWICE.md`, and `agents/openai.yaml`; defer consumer rewrites to U-03 and U-04.

## Acceptance Criteria
- [ ] The four artifacts form a self-contained, linked skill with valid frontmatter and Codex metadata.
- [ ] Vocabulary has one clear owner and does not claim implementation, review, or scheduler authority.
- [ ] Link and metadata tests cover every packaged artifact.

## Frontier
Ready; no dependency or human decision remains.

## Step-by-Step Implementation Plan
1. Reconcile the pinned upstream vocabulary with local ownership and terminology.
2. Add the four packaged artifacts with reciprocal internal links.
3. Validate frontmatter, invocation metadata, and references without rewriting consumers.

## Testing Plan
Run focused static skill-contract, metadata, and Markdown-link checks.

## Out of Scope
- Rewriting `tdd` or architecture-improvement consumers.
- Adding an execution orchestrator or scheduler behavior.
