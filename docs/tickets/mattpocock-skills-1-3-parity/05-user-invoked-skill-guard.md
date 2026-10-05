---
ticket_schema: 1
ticket_id: "MP13-05"
execution_mode: AFK
blocked_by: []
---

# MP13-05 — User-invoked skill guard

## Artifact Graph
- Artifact ID: `artifact:mattpocock-skills-1-3-parity-mp13-05`
- Role: `ticket`
- Parent: [mattpocock-skills-1-3-parity.md](../../specs/mattpocock-skills-1-3-parity.md)

## Parent Spec
[mattpocock-skills-1-3-parity.md](../../specs/mattpocock-skills-1-3-parity.md): Upstream delta, Follow-ups.

## What to Build
A skill with `disable-model-invocation: true` (today: `grill-me`, `grill-with-docs`, `handoff`,
`resolving-merge-conflicts`, `retro`, `ticket-driver`, `to-questionnaire`, `wait-what`, `wizard`)
is hidden from the model: only the human can start it. An instruction in another skill such as
"then use [handoff](../handoff/SKILL.md)" cannot work, because the agent cannot load it. Upstream
fixed six such call sites in 1.3 (#880). Add a test that finds every link from one skill's
`SKILL.md` or `references/*.md` to a user-invoked skill and fails unless the line tells the human
to run it or explicitly says the skill is not to be used.

## Acceptance Criteria
- [ ] The user-invoked set is read from front matter, not hard-coded.
- [ ] The test passes on current `main` (the only reference today, in `ticket-autopilot/SKILL.md`,
      says `handoff` is not a leaf-context channel).
- [ ] A fixture proves the test fails on an instruction like "then use the handoff skill".

## Frontier
Ready; no blocker. Files: one new test file only (MP13-04 does not edit it).

## Step-by-Step Implementation Plan
1. Collect user-invoked skill names from front matter.
2. Scan other skills' `SKILL.md` and `references/*.md` for links or backticked names.
3. Allow lines that address the human (for example "ask the user to run") or negate use.
4. Add the failing fixture case and the passing repository case.

## Testing Plan
Run the new test; `ruff check` on it; `npm run lint`.

## Out of Scope
- Changing which skills are user-invoked (`docs/model-invocation-policy.md` owns that).
- Rewording existing skills, unless the test finds a real violation.
