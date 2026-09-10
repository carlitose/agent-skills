---
type: source
title: "Adopt writing-for-agents"
identity_key: ticket:mattpocock-skills-adoption/U-05
identity_strength: stable
source_path: docs/tickets/mattpocock-skills-adoption/done/05-adopt-writing-for-agents.md
source_digest: sha256:9d19b994e4d22afa86848b2208713a9d304750aecfd5fee394525e54b6c87516
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-08
created_provenance: git-commit
disposition_changed: 2026-08-09
disposition_changed_provenance: git-rename
run_id: b9aeeb5529b642fd
---

# Adopt writing-for-agents

Compiled from `docs/tickets/mattpocock-skills-adoption/done/05-adopt-writing-for-agents.md`. Identity is `ticket:mattpocock-skills-adoption/U-05`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-08** via `git-commit`
- Disposition changed: **2026-08-09** via `git-rename`

## Run

Completed under autopilot run `b9aeeb5529b642fd`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-mattpocock-skills-adoption-u-05.md","payload_bytes":1353,"payload_sha256":"9d19b994e4d22afa86848b2208713a9d304750aecfd5fee394525e54b6c87516"}],"payload_bytes":1353,"payload_sha256":"9d19b994e4d22afa86848b2208713a9d304750aecfd5fee394525e54b6c87516","schema":1,"source_digest":"sha256:9d19b994e4d22afa86848b2208713a9d304750aecfd5fee394525e54b6c87516","source_identity":"ticket:mattpocock-skills-adoption/U-05","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1353,"payload_sha256":"9d19b994e4d22afa86848b2208713a9d304750aecfd5fee394525e54b6c87516","schema":1,"source_digest":"sha256:9d19b994e4d22afa86848b2208713a9d304750aecfd5fee394525e54b6c87516","source_identity":"ticket:mattpocock-skills-adoption/U-05"} -->
```markdown
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

```
