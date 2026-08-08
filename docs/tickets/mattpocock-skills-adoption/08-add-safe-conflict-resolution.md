---
ticket_schema: 1
ticket_id: "U-08"
execution_mode: AFK
blocked_by: []
---

# Add safe intent-based conflict resolution

## Parent Spec
[Open GitHub Issues Remediation](../../specs/open-github-issues-wayfinder.md)

## Adoption Source
[OI-07 approved parity selection](../../research/mattpocock-skills-parity.md#oi-07-approved-adoption-selection)

## What to Build
Add a merge-conflict resolution skill that traces both sides' intent and resolves compatible hunks with validation. Abort, staging, commit, rebase continuation, or scheduler-worktree mutation requires explicit caller authority; ambiguous incompatible intent gates.

## Acceptance Criteria
- [ ] Each resolution records both intents and verifies the combined behavior.
- [ ] Incompatible or insufficiently evidenced intent stops without destructive fallback.
- [ ] The skill never assumes authority to abort, commit, continue a rebase, or mutate a scheduler-owned worktree.
- [ ] Synthetic repository tests cover compatible, incompatible, and unauthorized operations.

## Frontier
Ready; no dependency or human decision remains for implementation.

## Step-by-Step Implementation Plan
1. Define read-only discovery and explicit mutation-authority boundaries.
2. Add the skill and metadata with hunk-by-hunk intent tracing.
3. Build synthetic conflict fixtures and prove no-commit/no-continuation defaults.

## Testing Plan
Use disposable Git repositories; compare refs, index, and worktree before rejected operations and run focused behavior checks after authorized resolution.

## Out of Scope
- Automatic commit, push, rebase continuation, or scheduler recovery.
- A blanket “never abort” or “always resolve” policy.
