---
type: source
title: "Move rare operational procedures behind clear prompt references"
identity_key: ticket:autopilot-practical-reliability/APM-07
identity_strength: stable
source_path: docs/tickets/autopilot-practical-reliability/done/07-progressive-references.md
source_digest: sha256:8979de78c0b91b0260ae7790eb9d65a01d9fe53deb4cf8fc931bde563ef0dcb6
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-07
created_provenance: git-commit
disposition_changed: 2026-09-08
disposition_changed_provenance: git-rename
run_id: practical-references-apm07-20260908
---

# Move rare operational procedures behind clear prompt references

Compiled from `docs/tickets/autopilot-practical-reliability/done/07-progressive-references.md`. Identity is `ticket:autopilot-practical-reliability/APM-07`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-07** via `git-commit`
- Disposition changed: **2026-09-08** via `git-rename`

## Graph

- Parent source: [[sources/artifact-autopilot-practical-reliability]]
- Blocked by: [[sources/ticket-autopilot-practical-reliability-apm-01]] — `ticket:autopilot-practical-reliability/APM-01`

## Run

Completed under autopilot run `practical-references-apm07-20260908`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-practical-reliability-apm-07.md","payload_bytes":3088,"payload_sha256":"8979de78c0b91b0260ae7790eb9d65a01d9fe53deb4cf8fc931bde563ef0dcb6"}],"payload_bytes":3088,"payload_sha256":"8979de78c0b91b0260ae7790eb9d65a01d9fe53deb4cf8fc931bde563ef0dcb6","schema":1,"source_digest":"sha256:8979de78c0b91b0260ae7790eb9d65a01d9fe53deb4cf8fc931bde563ef0dcb6","source_identity":"ticket:autopilot-practical-reliability/APM-07","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3088,"payload_sha256":"8979de78c0b91b0260ae7790eb9d65a01d9fe53deb4cf8fc931bde563ef0dcb6","schema":1,"source_digest":"sha256:8979de78c0b91b0260ae7790eb9d65a01d9fe53deb4cf8fc931bde563ef0dcb6","source_identity":"ticket:autopilot-practical-reliability/APM-07"} -->
```markdown
---
ticket_schema: 1
ticket_id: "APM-07"
execution_mode: AFK
blocked_by:
  - "APM-01"
---

# Move rare operational procedures behind clear prompt references

## Artifact Graph
- Artifact ID: `artifact:autopilot-practical-reliability-apm-07`
- Role: `ticket`
- Parent: [Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md)

## Parent Spec
[Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md) — S7 — Progressive Operational References.

## What to Build
Make the common Ticket Autopilot prompt easier to navigate by moving infrequent operational procedures from large paragraphs into owned, trigger-based references. Apply writing-for-agents while preserving APM-01's practical defaults and every current workflow/authority requirement.

## Acceptance Criteria
- [ ] SKILL.md retains the common workflow, ownership, required stop conditions, and practical defaults; each moved branch has an explicit retrieval trigger and a resolving local reference.
- [ ] Every supported command/procedure remains discoverable. No semantic gate, required verification, or authority rule disappears through editorial shortening.
- [ ] README and skill references identify one owner per rule instead of restating long competing procedures.
- [ ] Existing skill graph and forward scenarios still reach the appropriate procedure; normal ticket work does not need to load unrelated bootstrap/cleanup/Pi-sync detail.
- [ ] Existing context-budget tooling records normalized UTF-8 bytes before and after, with exclusions stated. No live token/cost savings are fabricated and no ceiling is raised merely to pass checks.

## Frontier
Dependency-blocked by APM-01.

Execute inline. AFK does not authorize subagents; explicit user request is required. This ticket does not authorize provider publication or merge.

## Step-by-Step Implementation Plan
1. Measure the current common prompt and workflow closure, then classify paragraphs by common versus infrequent branch using writing-for-agents.
2. Move branch-owned procedures into focused references and replace them with trigger-based pointers, retaining the common path and safety-critical decision points.
3. Reconcile duplicate README/prompt wording with the owning references and preserve APM-01's explicit-user-only delegation default.
4. Run link/skill graph/forward/context checks and document measured byte changes without converting them into token estimates.

## Testing Plan
- Routing/readability scenarios for ordinary execution and explicit merge, reconciliation, cleanup, bootstrap, and local-sync requests; no provider mutation.
- Local reference integrity, existing workflow forward tests, and before/after context measurements with missing data reported explicitly.

These are planned checks, not evidence that implementation or verification has occurred.

## Out of Scope
- Changing workflow semantics, adding security procedures, or broad unrelated skill rewrites.
- Replacing existing context-budget units or duplicating the separate live-token investigation.

```
