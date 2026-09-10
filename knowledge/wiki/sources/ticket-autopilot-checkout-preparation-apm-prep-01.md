---
type: source
title: "Rebind the existing wiki to the selected Windows checkout"
identity_key: ticket:autopilot-checkout-preparation/APM-PREP-01
identity_strength: stable
source_path: docs/tickets/autopilot-checkout-preparation/done/01-rebind-wiki.md
source_digest: sha256:114ffea14909d1404b1add303501e616ef5b0836113dfcbbefa0982e6b7f9c2a
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-07
created_provenance: git-commit
disposition_changed: 2026-09-07
disposition_changed_provenance: git-rename
run_id: apm-checkout-preparation
---

# Rebind the existing wiki to the selected Windows checkout

Compiled from `docs/tickets/autopilot-checkout-preparation/done/01-rebind-wiki.md`. Identity is `ticket:autopilot-checkout-preparation/APM-PREP-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-07** via `git-commit`
- Disposition changed: **2026-09-07** via `git-rename`

## Graph

- Parent source: [[sources/artifact-autopilot-practical-reliability]]

## Run

Completed under autopilot run `apm-checkout-preparation`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-autopilot-checkout-preparation-apm-prep-01.md","payload_bytes":2978,"payload_sha256":"114ffea14909d1404b1add303501e616ef5b0836113dfcbbefa0982e6b7f9c2a"}],"payload_bytes":2978,"payload_sha256":"114ffea14909d1404b1add303501e616ef5b0836113dfcbbefa0982e6b7f9c2a","schema":1,"source_digest":"sha256:114ffea14909d1404b1add303501e616ef5b0836113dfcbbefa0982e6b7f9c2a","source_identity":"ticket:autopilot-checkout-preparation/APM-PREP-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2978,"payload_sha256":"114ffea14909d1404b1add303501e616ef5b0836113dfcbbefa0982e6b7f9c2a","schema":1,"source_digest":"sha256:114ffea14909d1404b1add303501e616ef5b0836113dfcbbefa0982e6b7f9c2a","source_identity":"ticket:autopilot-checkout-preparation/APM-PREP-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "APM-PREP-01"
execution_mode: AFK
blocked_by: []
---

# Rebind the existing wiki to the selected Windows checkout

## Artifact Graph
- Artifact ID: `artifact:autopilot-checkout-preparation-apm-prep-01`
- Role: `ticket`
- Parent: [Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md)

## Parent Spec
[Practical Reliability for Ticket Autopilot](../../specs/autopilot-practical-reliability.md), S0 — Checkout Preparation.

## What to Build
Change only `project_root` in `knowledge/llm-wiki-project.json` from the nonexistent Mac checkout to `C:/Users/rdpuser/projects/agent-skills`, as explicitly requested by the user. Preserve existing configuration and use the existing resolver rather than changing application behavior.

## Acceptance Criteria
- [ ] The resolver returns the selected existing Windows checkout even when invoked from a different cwd.
- [ ] `schema`, `auto_sync`, `docs_globs`, `git_mode`, and `session_providers` are unchanged; `project_root` is the only changed JSON value.
- [ ] Git recognizes the resolved project and its committed APM spec/ticket sources; artifact discovery includes the eight implementation tickets.
- [ ] No generated wiki pages, raw sources, prompt files, installed copies, or global settings are part of this configuration candidate.
- [ ] A follow-up sync no longer fails for the obsolete Mac project root; unrelated lint/provider/publication failures remain visible and do not justify widening this change.

## Frontier
Ready after the parent spec and canonical ticket sources have been committed as planning inputs. Execute inline; no subagents are authorized or needed.

## Step-by-Step Implementation Plan
1. Read the original binding and the existing `read_binding`, `resolve_project_root`, and artifact-discovery behavior. Capture the broken-root baseline.
2. Update only the configured `project_root` in the isolated runner candidate.
3. Check exact configuration parity, resolution from another cwd, Git identity, and discovery of the committed APM sources.
4. Run the ticket-local quality stages and return the config-only candidate to the runner. Keep any generated wiki candidate separate.

## Testing Plan
- Local integration: existing binding resolver against the actual selected checkout, including invocation from a temporary cwd.
- Exact JSON before/after comparison allowing only `project_root`, and real Git tracking/discovery checks.
- Run existing project-binding tests. Report any later wiki lint issue separately; these planned checks are not evidence until executed.

## Out of Scope
- Portable relative-root support, binding-schema changes, automatic fallback, or a new configuration mechanism.
- Executing APM-01 through APM-08, modifying historical wiki references, or generating wiki pages in this ticket's diff.
- Changing global Git/Pi settings, creating a subagent, or claiming full wiki synchronization from binding-only checks.

```
