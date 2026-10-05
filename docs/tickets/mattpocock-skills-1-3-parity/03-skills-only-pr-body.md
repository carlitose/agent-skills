---
ticket_schema: 1
ticket_id: "MP13-03"
execution_mode: AFK
blocked_by: []
---

# MP13-03 — Skills-only PR body

## Artifact Graph
- Artifact ID: `artifact:mattpocock-skills-1-3-parity-mp13-03`
- Role: `ticket`
- Parent: [mattpocock-skills-1-3-parity.md](../../specs/mattpocock-skills-1-3-parity.md)

## Parent Spec
[mattpocock-skills-1-3-parity.md](../../specs/mattpocock-skills-1-3-parity.md): Upstream delta, Decision 3.

## What to Build
Extend the short PR body of the skills-only lane, adapted from upstream `pr`: a **Summary** with
the smallest visual that makes the change clear (pseudocode, call tree, file tree, Mermaid, or a
diff sketch), **Evidence** as before/after (failing then passing check, or output), **Merge danger**
(one-way or two-way door, plus blast radius in a few words), then the existing checks and open
gates. The body stays short.

## Acceptance Criteria
- [ ] The "Separately authorized delivery" section of `execute-ticket/references/skills-only.md`
      defines the PR body template with Summary, Evidence, Merge danger, Checks, Open gates.
- [ ] It says to pick one visual (at most two) and to skip a section rather than invent evidence;
      not-run checks stay visible.
- [ ] `explain-pr`, the Verification Record, and the Autopilot PR-body contract are unchanged.

## Frontier
Ready; no blocker. Files: `execute-ticket/references/skills-only.md` only.

## Step-by-Step Implementation Plan
1. Replace "Write a short PR body (summary, checks, open gates)" with a compact template.
2. Add the one-way/two-way door definition in one sentence and credit upstream `pr`.

## Testing Plan
Run any test that reads `skills-only.md` (grep the tests for it) and the artifact audit. Manual:
write the body of this ticket's own PR with the new template.

## Out of Scope
- Screenshots or other tooling for evidence capture.
- Changes to `explain-pr`, `validate-pr`, or the Autopilot delivery body.
