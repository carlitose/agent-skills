---
type: source
title: "MP13-04 — Domain-modeling triggers"
identity_key: ticket:mattpocock-skills-1-3-parity/MP13-04
identity_strength: stable
source_path: docs/tickets/mattpocock-skills-1-3-parity/04-domain-modeling-triggers.md
source_digest: sha256:14af469111a6ec888c02ac1737f8026f1a4de84431ef2f5f2e9a3d0ecf8c013b
source_status: present
artefact_kind: ticket
disposition: open
created: 2026-10-05
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# MP13-04 — Domain-modeling triggers

Compiled from `docs/tickets/mattpocock-skills-1-3-parity/04-domain-modeling-triggers.md`. Identity is `ticket:mattpocock-skills-1-3-parity/MP13-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-10-05** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-mattpocock-skills-1-3-parity]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-mattpocock-skills-1-3-parity-mp13-04.md","payload_bytes":1967,"payload_sha256":"14af469111a6ec888c02ac1737f8026f1a4de84431ef2f5f2e9a3d0ecf8c013b"}],"payload_bytes":1967,"payload_sha256":"14af469111a6ec888c02ac1737f8026f1a4de84431ef2f5f2e9a3d0ecf8c013b","schema":1,"source_digest":"sha256:14af469111a6ec888c02ac1737f8026f1a4de84431ef2f5f2e9a3d0ecf8c013b","source_identity":"ticket:mattpocock-skills-1-3-parity/MP13-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1967,"payload_sha256":"14af469111a6ec888c02ac1737f8026f1a4de84431ef2f5f2e9a3d0ecf8c013b","schema":1,"source_digest":"sha256:14af469111a6ec888c02ac1737f8026f1a4de84431ef2f5f2e9a3d0ecf8c013b","source_identity":"ticket:mattpocock-skills-1-3-parity/MP13-04"} -->
```markdown
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

```
