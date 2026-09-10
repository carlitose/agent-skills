---
type: source
title: "Adopt the shared codebase-design reference"
identity_key: ticket:mattpocock-skills-adoption/U-02
identity_strength: stable
source_path: docs/tickets/mattpocock-skills-adoption/done/02-adopt-codebase-design.md
source_digest: sha256:8731fc6f8a8a902de72902c9b0ace1a218571afe6111d9b03b543c7aa3450fa6
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-08
created_provenance: git-commit
disposition_changed: 2026-08-09
disposition_changed_provenance: git-rename
run_id: 403b2e32460f4b18
---

# Adopt the shared codebase-design reference

Compiled from `docs/tickets/mattpocock-skills-adoption/done/02-adopt-codebase-design.md`. Identity is `ticket:mattpocock-skills-adoption/U-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-08** via `git-commit`
- Disposition changed: **2026-08-09** via `git-rename`

## Run

Completed under autopilot run `403b2e32460f4b18`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-mattpocock-skills-adoption-u-02.md","payload_bytes":1457,"payload_sha256":"8731fc6f8a8a902de72902c9b0ace1a218571afe6111d9b03b543c7aa3450fa6"}],"payload_bytes":1457,"payload_sha256":"8731fc6f8a8a902de72902c9b0ace1a218571afe6111d9b03b543c7aa3450fa6","schema":1,"source_digest":"sha256:8731fc6f8a8a902de72902c9b0ace1a218571afe6111d9b03b543c7aa3450fa6","source_identity":"ticket:mattpocock-skills-adoption/U-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":1457,"payload_sha256":"8731fc6f8a8a902de72902c9b0ace1a218571afe6111d9b03b543c7aa3450fa6","schema":1,"source_digest":"sha256:8731fc6f8a8a902de72902c9b0ace1a218571afe6111d9b03b543c7aa3450fa6","source_identity":"ticket:mattpocock-skills-adoption/U-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "U-02"
execution_mode: AFK
blocked_by: []
---

# Adopt the shared codebase-design reference

## Parent Spec
[Open GitHub Issues Remediation](../../specs/open-github-issues-wayfinder.md)

## Adoption Source
[OI-07 approved parity selection](../../research/mattpocock-skills-parity.md#oi-07-approved-adoption-selection)

## What to Build
Add `codebase-design` as the single shared vocabulary owner for modules, interfaces, depth, seams, and adapters. Package `SKILL.md`, `DEEPENING.md`, `DESIGN-IT-TWICE.md`, and `agents/openai.yaml`; defer consumer rewrites to U-03 and U-04.

## Acceptance Criteria
- [ ] The four artifacts form a self-contained, linked skill with valid frontmatter and Codex metadata.
- [ ] Vocabulary has one clear owner and does not claim implementation, review, or scheduler authority.
- [ ] Link and metadata tests cover every packaged artifact.

## Frontier
Ready; no dependency or human decision remains.

## Step-by-Step Implementation Plan
1. Reconcile the pinned upstream vocabulary with local ownership and terminology.
2. Add the four packaged artifacts with reciprocal internal links.
3. Validate frontmatter, invocation metadata, and references without rewriting consumers.

## Testing Plan
Run focused static skill-contract, metadata, and Markdown-link checks.

## Out of Scope
- Rewriting `tdd` or architecture-improvement consumers.
- Adding an execution orchestrator or scheduler behavior.

```
