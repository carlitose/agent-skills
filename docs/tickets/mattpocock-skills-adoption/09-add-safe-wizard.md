---
ticket_schema: 1
ticket_id: "U-09"
execution_mode: AFK
blocked_by: []
---

# Add a safe human-run wizard template

## Parent Spec
[Open GitHub Issues Remediation](../../specs/open-github-issues-wayfinder.md)

## Adoption Source
[OI-07 approved parity selection](../../research/mattpocock-skills-parity.md#oi-07-approved-adoption-selection)

## What to Build
Add a wizard skill, `template.sh`, and Codex metadata using stage counts instead of time estimates, hidden input for sensitive values, idempotent environment updates, and cross-platform URL opening. Live wizard execution is explicitly human-run; automated fixtures must disable provider and browser effects.

## Acceptance Criteria
- [ ] Progress uses deterministic stage counts and no duration estimate.
- [ ] Sensitive input is hidden and never echoed or embedded in test artifacts.
- [ ] Environment updates are idempotent and external/provider/browser actions require explicit human execution.
- [ ] Fixture mode proves it cannot call `gh`, a provider, or a browser.

## Frontier
Ready; no dependency or human decision remains for implementation.

## Step-by-Step Implementation Plan
1. Adapt the pinned template to local safety and portability boundaries.
2. Add a non-mutating fixture mode before any live integration path.
3. Add metadata and tests for syntax, idempotence, hidden input, and disabled side effects.

## Testing Plan
Run `bash -n`, `shellcheck` when available, static metadata/link tests, and a fixture with fake environment/provider/browser commands.

## Out of Scope
- Running a live setup wizard during AFK ticket implementation.
- Unattended `.env`, credential-store, provider, or browser mutation.
