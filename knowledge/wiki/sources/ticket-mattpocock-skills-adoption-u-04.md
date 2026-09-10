---
type: source
title: "Scope architecture improvement with shared design vocabulary"
identity_key: ticket:mattpocock-skills-adoption/U-04
identity_strength: stable
source_path: docs/tickets/mattpocock-skills-adoption/done/04-scope-architecture-improvement.md
source_digest: sha256:510e81beafab7675e37d224e826b97f50ae7730286999a5ec3cd1c6d9c0ac552
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-08
created_provenance: git-commit
disposition_changed: 2026-08-09
disposition_changed_provenance: git-rename
run_id: 1cb9ef0a18264640
---

# Scope architecture improvement with shared design vocabulary

Compiled from `docs/tickets/mattpocock-skills-adoption/done/04-scope-architecture-improvement.md`. Identity is `ticket:mattpocock-skills-adoption/U-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-08** via `git-commit`
- Disposition changed: **2026-08-09** via `git-rename`

## Graph

- Blocked by: [[sources/ticket-mattpocock-skills-adoption-u-02]] — `ticket:mattpocock-skills-adoption/U-02`

## Run

Completed under autopilot run `1cb9ef0a18264640`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-mattpocock-skills-adoption-u-04.md","payload_bytes":2191,"payload_sha256":"510e81beafab7675e37d224e826b97f50ae7730286999a5ec3cd1c6d9c0ac552"}],"payload_bytes":2191,"payload_sha256":"510e81beafab7675e37d224e826b97f50ae7730286999a5ec3cd1c6d9c0ac552","schema":1,"source_digest":"sha256:510e81beafab7675e37d224e826b97f50ae7730286999a5ec3cd1c6d9c0ac552","source_identity":"ticket:mattpocock-skills-adoption/U-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2191,"payload_sha256":"510e81beafab7675e37d224e826b97f50ae7730286999a5ec3cd1c6d9c0ac552","schema":1,"source_digest":"sha256:510e81beafab7675e37d224e826b97f50ae7730286999a5ec3cd1c6d9c0ac552","source_identity":"ticket:mattpocock-skills-adoption/U-04"} -->
```markdown
---
ticket_schema: 1
ticket_id: "U-04"
execution_mode: HITL
blocked_by:
  - "U-02"
---

# Scope architecture improvement with shared design vocabulary

## Parent Spec
[Open GitHub Issues Remediation](../../specs/open-github-issues-wayfinder.md)

## Adoption Source
[OI-07 approved parity selection](../../research/mattpocock-skills-parity.md#oi-07-approved-adoption-selection)

## What to Build
Update `improve-codebase-architecture` to consume U-02 `codebase-design` terminology and start from recent-change hot spots before widening by evidence. Preserve `improve-codebase-architecture` as the bounded survey owner and `codebase-improver` as the separate human-gated full-repository workflow. Ask one human question before deciding whether the temporary visual report is a stable output or an optional ephemeral aid.

## Acceptance Criteria
- [ ] Shared design terms link to U-02 rather than being redefined locally.
- [ ] Default discovery considers recent changes and documents when evidence justifies a wider scan.
- [ ] The visual-report stability decision is explicitly confirmed and reflected in docs/tests before its output contract changes.
- [ ] No routing behavior from OI-08 or execution/AgentTool/isolation behavior from OI-09 is duplicated.
- [ ] `codebase-improver` ownership and human gate remain unchanged.

## Frontier
Dependency-blocked by U-02; then HITL on whether the visual report is stable or ephemeral.

## Step-by-Step Implementation Plan
1. Replace duplicated design language with links to U-02.
2. Add recent-change-first scoping with an evidence-based widening rule.
3. Present the visual-report tradeoff as one canonical human decision and wait for confirmation.
4. Implement and test only the confirmed output contract while preserving both local owners.

## Testing Plan
Run static ownership/link/scoping tests. If a stable report is approved, add a bounded render smoke test; otherwise verify the ephemeral path is not claimed as a durable contract.

## Out of Scope
- Wayfinder-to-Grilling routing owned by OI-08.
- AgentTool-optional composition, execution isolation, or authority vocabulary owned by OI-09.
- Folding `codebase-improver` into this skill.

```
