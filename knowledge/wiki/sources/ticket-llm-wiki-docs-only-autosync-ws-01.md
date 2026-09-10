---
type: source
title: "Map the existing wiki sync and docs-only boundary"
identity_key: ticket:llm-wiki-docs-only-autosync/WS-01
identity_strength: stable
source_path: docs/tickets/llm-wiki-docs-only-autosync/done/01-map-current-sync-boundary.md
source_digest: sha256:7f12037669571e3e1998b78346425ef6bc0ef33e9c26d0d73cd0fb902e3e8c64
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-28
created_provenance: git-commit
disposition_changed: 2026-08-28
disposition_changed_provenance: git-rename
run_id: f74e8975ae4d49a5
---

# Map the existing wiki sync and docs-only boundary

Compiled from `docs/tickets/llm-wiki-docs-only-autosync/done/01-map-current-sync-boundary.md`. Identity is `ticket:llm-wiki-docs-only-autosync/WS-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-28** via `git-commit`
- Disposition changed: **2026-08-28** via `git-rename`

## Graph

- Parent source: [[sources/artifact-llm-wiki-docs-only-autosync-wayfinder]]

## Run

Completed under autopilot run `f74e8975ae4d49a5`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[5],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[4],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-docs-only-autosync-ws-01.md","payload_bytes":2611,"payload_sha256":"7f12037669571e3e1998b78346425ef6bc0ef33e9c26d0d73cd0fb902e3e8c64"}],"payload_bytes":2611,"payload_sha256":"7f12037669571e3e1998b78346425ef6bc0ef33e9c26d0d73cd0fb902e3e8c64","schema":1,"source_digest":"sha256:7f12037669571e3e1998b78346425ef6bc0ef33e9c26d0d73cd0fb902e3e8c64","source_identity":"ticket:llm-wiki-docs-only-autosync/WS-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 4: What to Build |
| acceptance | 5: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2611,"payload_sha256":"7f12037669571e3e1998b78346425ef6bc0ef33e9c26d0d73cd0fb902e3e8c64","schema":1,"source_digest":"sha256:7f12037669571e3e1998b78346425ef6bc0ef33e9c26d0d73cd0fb902e3e8c64","source_identity":"ticket:llm-wiki-docs-only-autosync/WS-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "WS-01"
execution_mode: AFK
blocked_by: []
---

# Map the existing wiki sync and docs-only boundary

## Artifact Graph
- Artifact ID: `artifact:ws-01-map-current-sync-boundary`
- Role: `ticket`
- Parent: [llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## Parent Spec
[llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## Produces
- `docs/research/llm-wiki-docs-only-autosync-contract.md`, which must point back to this ticket.

## What to Build
An evidence-backed research report that maps the current `llm-wiki`, `docs-only-adopt`,
`to-tickets`, and `ticket-autopilot` boundaries. It must distinguish an absent wiki, a bound
untracked wiki, a bound tracked wiki, and broken or ambiguous discovery without proposing
implementation as observed behavior.

## Acceptance Criteria
- [ ] The report identifies the current public commands, call sites, versioned contracts,
      and exact files that own discovery, project binding, docs-only path policy, candidate
      identity, integration state, and wiki validation.
- [ ] It proves whether project-to-wiki discovery exists and defines what evidence can
      classify generated wiki content as tracked, untracked, partial, or external.
- [ ] It traces both requested triggers: once after a complete `to-tickets` batch and once
      after durable `integrated` state in `ticket-autopilot`.
- [ ] It identifies every current invariant that a docs-only wiki profile must preserve,
      including mixed-candidate rejection and claim ceiling.
- [ ] Facts, inferences, unknowns, and recommended experiments are separated.

## Frontier
Ready. Its report is the evidence input for `WS-02`.

## Step-by-Step Implementation Plan
1. Inspect the binding, ingest, timeline, lint, docs-only contract, runner state, and caller
   code. Checkpoint: every claimed owner has a source path.
2. Model the state matrix and candidate identities. Checkpoint: absent, untracked, tracked,
   partial, external, multiple, and broken cases are accounted for.
3. Write the report with an Artifact Graph pointing to this ticket and update this ticket's
   `Produces` entry to a reciprocal Markdown link in the same change.

## Testing Plan
Run read-only CLI help, dry-run, and repository searches where useful. Verify every local
link and run the canonical artifact audit against the completed report/ticket graph.

## Out of Scope
- Implementing sync, changing docs-only policy, or mutating a real wiki.
- Choosing the unresolved HITL policy owned by `WS-03`.

```
