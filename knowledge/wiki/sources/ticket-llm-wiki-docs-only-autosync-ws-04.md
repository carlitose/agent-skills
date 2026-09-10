---
type: source
title: "Implement the idempotent sync-project boundary"
identity_key: ticket:llm-wiki-docs-only-autosync/WS-04
identity_strength: stable
source_path: docs/tickets/llm-wiki-docs-only-autosync/done/04-implement-sync-project.md
source_digest: sha256:f3487d0191f2ef6cc80b52ce9f33839aba04885bb3fd6f120df90c5232c2b118
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-28
created_provenance: git-commit
disposition_changed: 2026-08-28
disposition_changed_provenance: git-rename
run_id: f74e8975ae4d49a5
---

# Implement the idempotent sync-project boundary

Compiled from `docs/tickets/llm-wiki-docs-only-autosync/done/04-implement-sync-project.md`. Identity is `ticket:llm-wiki-docs-only-autosync/WS-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-28** via `git-commit`
- Disposition changed: **2026-08-28** via `git-rename`

## Graph

- Parent source: [[sources/artifact-llm-wiki-docs-only-autosync-wayfinder]]
- Blocked by: [[sources/ticket-llm-wiki-docs-only-autosync-ws-03]] — `ticket:llm-wiki-docs-only-autosync/WS-03`

## Run

Completed under autopilot run `f74e8975ae4d49a5`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-docs-only-autosync-ws-04.md","payload_bytes":2066,"payload_sha256":"f3487d0191f2ef6cc80b52ce9f33839aba04885bb3fd6f120df90c5232c2b118"}],"payload_bytes":2066,"payload_sha256":"f3487d0191f2ef6cc80b52ce9f33839aba04885bb3fd6f120df90c5232c2b118","schema":1,"source_digest":"sha256:f3487d0191f2ef6cc80b52ce9f33839aba04885bb3fd6f120df90c5232c2b118","source_identity":"ticket:llm-wiki-docs-only-autosync/WS-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2066,"payload_sha256":"f3487d0191f2ef6cc80b52ce9f33839aba04885bb3fd6f120df90c5232c2b118","schema":1,"source_digest":"sha256:f3487d0191f2ef6cc80b52ce9f33839aba04885bb3fd6f120df90c5232c2b118","source_identity":"ticket:llm-wiki-docs-only-autosync/WS-04"} -->
```markdown
---
ticket_schema: 1
ticket_id: "WS-04"
execution_mode: AFK
blocked_by:
  - "WS-03"
---

# Implement the idempotent sync-project boundary

## Artifact Graph
- Artifact ID: `artifact:ws-04-implement-sync-project`
- Role: `ticket`
- Parent: [llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## Parent Spec
[llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## What to Build
One versioned `llm-wiki sync-project` capability that hides discovery, project-history
ingest, timeline rebuild, wiki validation, tracking classification, and normalized outcomes.
Implement the confirmed docs-only wiki profile at the same public boundary.

## Acceptance Criteria
- [ ] A single invocation returns the decision-spec result for every normal and error state.
- [ ] Repeating sync on unchanged inputs writes nothing and returns an unchanged result.
- [ ] Untracked output is validated directly; tracked output is returned as a frozen
      docs-only candidate and is not committed or delivered by `llm-wiki`.
- [ ] Mixed, partial, ambiguous, broken, stale, and concurrently changed inputs fail exactly
      as decided.
- [ ] Unit and integration tests prove command ordering, allowed paths, lint evidence,
      CandidateRef binding, and claim ceiling.

## Frontier
Blocked by confirmed decision `WS-03`. It unblocks both caller integrations.

## Step-by-Step Implementation Plan
1. Add the versioned result/request contracts and pure normalization tests.
2. Compose existing ingest, timeline, and lint owners behind one idempotent operation.
3. Add the docs-only profile adapter and tracked/untracked delivery seam.
4. Expose the CLI and update `llm-wiki` plus `ticket-autopilot` instructions.

## Testing Plan
Run focused unit tests for both packages and isolated Git integration fixtures for all
matrix states. Run the existing llm-wiki lint and docs-only suites unchanged.

## Out of Scope
- Caller triggers, provider PR creation, or automatic merge.
- Scaffolding a missing wiki.

```
