---
type: source
title: "Keep session digests in the wiki catalog"
identity_key: ticket:llm-wiki-agent-skills-ingest/AWI-01
identity_strength: stable
source_path: docs/tickets/llm-wiki-agent-skills-ingest/done/01-keep-session-digests-in-the-wiki-catalog.md
source_digest: sha256:10a7d5cd194cfc1d62e35c3eed9fa64eddea069998e6fa8ceb35785a8a11e8b2
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-31
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Keep session digests in the wiki catalog

Compiled from `docs/tickets/llm-wiki-agent-skills-ingest/done/01-keep-session-digests-in-the-wiki-catalog.md`. Identity is `ticket:llm-wiki-agent-skills-ingest/AWI-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-31** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-llm-wiki-agent-skills-ingest]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-agent-skills-ingest-awi-01.md","payload_bytes":3794,"payload_sha256":"10a7d5cd194cfc1d62e35c3eed9fa64eddea069998e6fa8ceb35785a8a11e8b2"}],"payload_bytes":3794,"payload_sha256":"10a7d5cd194cfc1d62e35c3eed9fa64eddea069998e6fa8ceb35785a8a11e8b2","schema":1,"source_digest":"sha256:10a7d5cd194cfc1d62e35c3eed9fa64eddea069998e6fa8ceb35785a8a11e8b2","source_identity":"ticket:llm-wiki-agent-skills-ingest/AWI-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3794,"payload_sha256":"10a7d5cd194cfc1d62e35c3eed9fa64eddea069998e6fa8ceb35785a8a11e8b2","schema":1,"source_digest":"sha256:10a7d5cd194cfc1d62e35c3eed9fa64eddea069998e6fa8ceb35785a8a11e8b2","source_identity":"ticket:llm-wiki-agent-skills-ingest/AWI-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "AWI-01"
execution_mode: AFK
blocked_by: []
---

# Keep session digests in the wiki catalog

## Artifact Graph

- Artifact ID: `artifact:awi-01-session-catalog`
- Role: `ticket`
- Parent: [Agent Skills Tracked Project Wiki Ingest](../../specs/llm-wiki-agent-skills-ingest.md)

## Parent Spec

[Agent Skills Tracked Project Wiki Ingest](../../specs/llm-wiki-agent-skills-ingest.md)

## What to Build

Implement the shared catalog contract from the parent spec before creating the durable wiki.
`session_ingest.py` must add or refresh a deterministic session-source section in
`wiki/index.md`, and `ingest_docs.py` must preserve/rebuild that section whenever project-doc
changes rebuild the rest of the index.

Adopt the accepted parent spec, its reciprocal parent-Wayfinder update, and both canonical AWI
tickets into the tracked candidate. The scheduler input may be an ignored planning source, but
the delivered repository must retain the planning provenance and an executable `AWI-02`.

## Acceptance Criteria

- [ ] A new or changed session digest appears exactly once under a deterministic `Session
      sources` section in `wiki/index.md`; order is stable and replay creates no duplicate.
- [ ] A later `ingest_docs.py` index rebuild preserves every existing regular
      `wiki/sources/session-*.md` entry exactly once.
- [ ] Session catalog refresh preserves project source sections and the reachable timeline
      catalog rather than rebuilding a competing index shape.
- [ ] A disposable scaffold → docs ingest → session ingest → timeline → docs re-ingest → lint
      integration case reports zero `index-drift` errors for session pages.
- [ ] Focused tests seed duplicate, missing, new, changed, and docs-rebuild cases and assert
      deterministic UTF-8 output.
- [ ] The accepted spec, parent reciprocal edge, `AWI-01` tracked completion-path mirror, and
      open `AWI-02` ticket are included in the candidate without changing Ticket Envelope v1.
- [ ] No provider, network, credential, application-private state, wiki instance, RAG component,
      or transcript content is introduced by this ticket.

## Frontier

Ready. The current implementation deterministically leaves every session digest outside the
catalog; the real disposable proof measured 208 resulting `index-drift` errors. `AWI-02` remains
blocked until this ticket integrates.

## Step-by-Step Implementation Plan

1. Isolate the index-section parsing/rendering needed to replace one generated session section
   without disturbing project and timeline sections.
2. Refresh that section after session writes and include all present session digest pages in
   stable order.
3. Extend project-doc index rebuild to discover and render the same present session pages.
4. Add unit tests for insertion, replay, duplicate repair, and preservation in both operation
   orders.
5. Add one temporary full-pipeline regression that reaches a zero-error catalog boundary.
6. Update the public wiki contract and planning artifacts only where the new ownership rule is
   externally relevant.

## Testing Plan

Run focused `llm-wiki` session, docs-ingest, index/lint, and sync tests; run a temporary scaffold
pipeline with synthetic sessions; run the complete `llm-wiki` suite; run Artifact Graph and
Markdown-link checks on the planning candidate. No live/provider test is applicable.

## Out of Scope

- Creating the tracked `knowledge/` instance.
- Changing session discovery, digest content, pointer fields, or transcript-selection policy.
- Deleting session pages when an external transcript disappears.
- Suppressing orphan warnings or treating a catalog entry as an inbound citation.
- Any retrieval, embedding, vector, graph-expansion, Obsidian-plugin, HTTP, or MCP feature.

```
