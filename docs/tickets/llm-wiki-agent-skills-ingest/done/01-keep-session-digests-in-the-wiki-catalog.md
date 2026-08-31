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
