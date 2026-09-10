---
type: source
title: "Forward-test the wiki auto-sync matrix"
identity_key: ticket:llm-wiki-docs-only-autosync/WS-07
identity_strength: stable
source_path: docs/tickets/llm-wiki-docs-only-autosync/done/07-forward-test-sync-matrix.md
source_digest: sha256:01390ace9b1abd0d8b8d55f6e5b19c492b203b6423fa71c92c70790d93d208e3
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-28
created_provenance: git-commit
disposition_changed: 2026-08-29
disposition_changed_provenance: git-rename
run_id: f74e8975ae4d49a5
---

# Forward-test the wiki auto-sync matrix

Compiled from `docs/tickets/llm-wiki-docs-only-autosync/done/07-forward-test-sync-matrix.md`. Identity is `ticket:llm-wiki-docs-only-autosync/WS-07`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-28** via `git-commit`
- Disposition changed: **2026-08-29** via `git-rename`

## Graph

- Parent source: [[sources/artifact-llm-wiki-docs-only-autosync-wayfinder]]
- Blocked by: [[sources/ticket-llm-wiki-docs-only-autosync-ws-05]] — `ticket:llm-wiki-docs-only-autosync/WS-05`
- Blocked by: [[sources/ticket-llm-wiki-docs-only-autosync-ws-06]] — `ticket:llm-wiki-docs-only-autosync/WS-06`

## Run

Completed under autopilot run `f74e8975ae4d49a5`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-docs-only-autosync-ws-07.md","payload_bytes":2094,"payload_sha256":"01390ace9b1abd0d8b8d55f6e5b19c492b203b6423fa71c92c70790d93d208e3"}],"payload_bytes":2094,"payload_sha256":"01390ace9b1abd0d8b8d55f6e5b19c492b203b6423fa71c92c70790d93d208e3","schema":1,"source_digest":"sha256:01390ace9b1abd0d8b8d55f6e5b19c492b203b6423fa71c92c70790d93d208e3","source_identity":"ticket:llm-wiki-docs-only-autosync/WS-07","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2094,"payload_sha256":"01390ace9b1abd0d8b8d55f6e5b19c492b203b6423fa71c92c70790d93d208e3","schema":1,"source_digest":"sha256:01390ace9b1abd0d8b8d55f6e5b19c492b203b6423fa71c92c70790d93d208e3","source_identity":"ticket:llm-wiki-docs-only-autosync/WS-07"} -->
```markdown
---
ticket_schema: 1
ticket_id: "WS-07"
execution_mode: AFK
blocked_by:
  - "WS-05"
  - "WS-06"
---

# Forward-test the wiki auto-sync matrix

## Artifact Graph
- Artifact ID: `artifact:ws-07-forward-test-sync-matrix`
- Role: `ticket`
- Parent: [llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## Parent Spec
[llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## What to Build
A deterministic forward-test suite and report proving the complete behavior of both triggers
across absent, untracked, tracked, and exceptional wiki states.

## Acceptance Criteria
- [ ] Ticket creation invokes sync once per batch; integration invokes sync once per durable
      integrated ticket effect.
- [ ] Absent is a no-op, untracked is directly validated, and tracked is a separate
      docs-only candidate with the expected claim ceiling.
- [ ] Partial tracking, multiple roots, broken binding, mixed paths, failed lint, concurrent
      change, resume, and retry all reach the decided result without silent fallback.
- [ ] No scenario scaffolds a wiki, mutates an application CandidateRef, bypasses merge
      authorization, or presents wiki content as primary evidence.
- [ ] The report records local simulation limitations and makes no live-provider claim.

## Frontier
Blocked by both caller integrations `WS-05` and `WS-06`.

## Step-by-Step Implementation Plan
1. Add raw scenario prompts/fixtures for every matrix row and trigger boundary.
2. Execute them through the public CLIs and capture normalized results.
3. Validate idempotency, Git isolation, evidence ceilings, and retry state.
4. Emit a machine-readable report and fold outcomes into the parent wayfinder.

## Testing Plan
Run the complete unit/integration suites plus the new forward-test scenarios. Provider and
production-wiki boundaries remain explicitly unobserved unless separately authorized.

## Out of Scope
- Live provider mutation or automatic merging during the forward test.
- New behavior beyond the confirmed `WS-03` decision.

```
