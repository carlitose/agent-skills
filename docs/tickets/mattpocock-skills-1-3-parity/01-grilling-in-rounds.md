---
ticket_schema: 1
ticket_id: "MP13-01"
execution_mode: AFK
blocked_by: []
---

# MP13-01 — Grilling in rounds

## Artifact Graph
- Artifact ID: `artifact:mattpocock-skills-1-3-parity-mp13-01`
- Role: `ticket`
- Parent: [mattpocock-skills-1-3-parity.md](../../specs/mattpocock-skills-1-3-parity.md)

## Parent Spec
[mattpocock-skills-1-3-parity.md](../../specs/mattpocock-skills-1-3-parity.md): Upstream delta, Decision 1.

## What to Build
Change `grilling` from one question per message to **rounds**: each round asks every question
whose prerequisites are settled, numbered, each with a recommended answer and a short reason,
separated by `---`. A question that depends on an answer still open in the round waits for a
later round. Align the callers that restate the old rule (`wayfinder` Destination gate,
`grill-with-docs`) so no skill still says "one question at a time".

## Acceptance Criteria
- [ ] `grilling/SKILL.md` defines the round, the frontier rule, and a round template
      (numbered questions, recommended answer each, `---` separator).
- [ ] The confirmation gate is unchanged: nothing is enacted before the user confirms shared
      understanding.
- [ ] `wayfinder/SKILL.md` and `grill-with-docs/SKILL.md` reference rounds, not single questions.
- [ ] `ticket-autopilot/tests/test_skill_graph.py` asserts the new wording instead of
      "Ask one question at a time and wait".

## Frontier
Ready; no blocker. Files: `grilling/SKILL.md`, `wayfinder/SKILL.md`, `grill-with-docs/SKILL.md`,
`ticket-autopilot/tests/test_skill_graph.py` (no other MP13 ticket edits them).

## Step-by-Step Implementation Plan
1. Rewrite the Core Rules and Workflow of `grilling` around rounds; add the template.
2. Update the `wayfinder` Destination gate line and the `grill-with-docs` summary line.
3. Update the wayfinder assertion in `test_skill_graph.py`.

## Testing Plan
Run `python -B -m pytest ticket-autopilot/tests/test_skill_graph.py -q`; grep the repo skills for
"one question at a time" (expect none). Manual: one short grilling round reads correctly.

## Out of Scope
- Sub-agent fact finding from upstream `grilling` (facts stay inline; no delegation).
- Changes to `grill-me` beyond what its text already inherits from `grilling`.
