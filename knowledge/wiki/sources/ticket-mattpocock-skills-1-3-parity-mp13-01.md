---
type: source
title: "MP13-01 — Grilling in rounds"
identity_key: ticket:mattpocock-skills-1-3-parity/MP13-01
identity_strength: stable
source_path: docs/tickets/mattpocock-skills-1-3-parity/01-grilling-in-rounds.md
source_digest: sha256:ff106c6afc38e73f021ca54e8e56960a2542e29cc8f42ff258ea10c3d8fa48c3
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# MP13-01 — Grilling in rounds

Compiled from `docs/tickets/mattpocock-skills-1-3-parity/01-grilling-in-rounds.md`. Identity is `ticket:mattpocock-skills-1-3-parity/MP13-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-mattpocock-skills-1-3-parity]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-mattpocock-skills-1-3-parity-mp13-01.md","payload_bytes":2252,"payload_sha256":"ff106c6afc38e73f021ca54e8e56960a2542e29cc8f42ff258ea10c3d8fa48c3"}],"payload_bytes":2252,"payload_sha256":"ff106c6afc38e73f021ca54e8e56960a2542e29cc8f42ff258ea10c3d8fa48c3","schema":1,"source_digest":"sha256:ff106c6afc38e73f021ca54e8e56960a2542e29cc8f42ff258ea10c3d8fa48c3","source_identity":"ticket:mattpocock-skills-1-3-parity/MP13-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2252,"payload_sha256":"ff106c6afc38e73f021ca54e8e56960a2542e29cc8f42ff258ea10c3d8fa48c3","schema":1,"source_digest":"sha256:ff106c6afc38e73f021ca54e8e56960a2542e29cc8f42ff258ea10c3d8fa48c3","source_identity":"ticket:mattpocock-skills-1-3-parity/MP13-01"} -->
```markdown
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

```
