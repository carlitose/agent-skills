---
ticket_schema: 1
ticket_id: "U-05"
execution_mode: AFK
blocked_by: []
---

# Adopt writing-for-agents

## Parent Spec
[Open GitHub Issues Remediation](../../specs/open-github-issues-wayfinder.md)

## Adoption Source
[OI-07 approved parity selection](../../research/mattpocock-skills-parity.md#oi-07-approved-adoption-selection)

## What to Build
Add `writing-for-agents` with its mechanics reference and Codex metadata. Own writing clarity, pointers, information hierarchy, completion criteria, leading words, and pruning; remain subordinate to the existing skill scaffold owner.

## Acceptance Criteria
- [ ] `SKILL.md`, `SKILL-MECHANICS.md`, and `agents/openai.yaml` are linked and valid.
- [ ] Metadata permits the intended implicit invocation without claiming scaffolding ownership.
- [ ] Examples distinguish concise agent-facing guidance from a new skill-generation workflow.

## Frontier
Ready; no dependency or human decision remains.

## Step-by-Step Implementation Plan
1. Adapt the pinned mechanics to local terminology and ownership.
2. Add metadata and invocation examples.
3. Add frontmatter, trigger, and link tests.

## Testing Plan
Run focused metadata/frontmatter/link tests and the static ownership graph.

## Out of Scope
- Replacing `skill-creator` or another scaffold owner.
- Rewriting unrelated skills in the adoption slice.
