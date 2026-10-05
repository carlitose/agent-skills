---
ticket_schema: 1
ticket_id: "MP13-04"
execution_mode: AFK
blocked_by: []
---

# MP13-04 — Domain-modeling triggers

## Artifact Graph
- Artifact ID: `artifact:mattpocock-skills-1-3-parity-mp13-04`
- Role: `ticket`
- Parent: [mattpocock-skills-1-3-parity.md](../../specs/mattpocock-skills-1-3-parity.md)

## Parent Spec
[mattpocock-skills-1-3-parity.md](../../specs/mattpocock-skills-1-3-parity.md): Upstream delta, Follow-ups.

## What to Build
Today the `domain-modeling` description fires when "the user wants" glossary or ADR work. Upstream
1.3 fires it on the situation instead: discussing codebase terminology, editing the glossary, or
recording or editing an ADR. Rewrite our description the same way, keeping our file names
(`CONTEXT.md`, `CONTEXT-MAP.md`, `docs/adr/`), so the skill also loads when the agent itself is
about to touch those files.

## Acceptance Criteria
- [ ] The description names the triggers: discussing codebase or domain terminology, writing or
      editing `CONTEXT.md`, recording or editing an ADR.
- [ ] No `GLOSSARY.md` rename; the skill body is unchanged.
- [ ] A test asserts the three triggers in the description.
- [ ] Any fixed context-budget byte baseline is updated to the measured value, with the reason.

## Frontier
Ready; no blocker. Files: `domain-modeling/SKILL.md`, its test, and any listing-byte baseline in
`ticket-autopilot/tests/test_context_budget.py` (MP13-05 does not edit these).

## Step-by-Step Implementation Plan
1. Add the failing description assertion.
2. Rewrite the description in one sentence plus triggers.
3. Run the context-budget tests and update the measured baseline only if it moved.

## Testing Plan
`python -B -m pytest ticket-autopilot/tests/test_skill_graph.py ticket-autopilot/tests/test_context_budget.py ticket-autopilot/tests/test_token_reduction_guide.py -q`; `npm run lint`.

## Out of Scope
- Renaming `CONTEXT.md` to `GLOSSARY.md`.
- Changes to the domain-modeling procedure.
