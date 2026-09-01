---
ticket_schema: 1
ticket_id: "OHR-01"
execution_mode: AFK
blocked_by: []
---

# Research source-to-contract compatibility for the Obsidian notes

## Artifact Graph

- Artifact ID: `artifact:ohr-01-source-contract-compatibility`
- Role: `ticket`
- Parent: [Obsidian-First LLM Wiki with Measured Hybrid Retrieval](../../specs/llm-wiki-obsidian-hybrid-retrieval-wayfinder.md)

## Parent Spec

[Obsidian-First LLM Wiki with Measured Hybrid Retrieval](../../specs/llm-wiki-obsidian-hybrid-retrieval-wayfinder.md)

## Produces

- [Obsidian source-to-contract compatibility report](../../research/llm-wiki-obsidian-source-contract-compatibility.md)

## What to Build

Publish the accepted wayfinder map and produce one evidence-backed compatibility report over the three local source notes, the current `llm-wiki` contract, and accepted application-independence decisions. Separate behavior that is reusable now, claims that contradict or exceed the accepted contract, bounded architecture candidates, and unknowns that OHR-03 must decide. This is research, not source ingest or production architecture selection.

## Acceptance Criteria

- [ ] The report identifies each source by exact local path, byte digest, and observed scope without copying source content into the repository or a durable wiki.
- [ ] Every material source claim has a line- or heading-level citation to the note, and every current-contract claim cites the exact repository document or implementation seam inspected.
- [ ] A compatibility matrix distinguishes `reuse-now`, `compatible-candidate`, `contradiction`, `unobserved`, and `human-decision-required`; configured-but-unused HTTP or MCP surfaces are not called active.
- [ ] The report evaluates Markdown/front matter/wikilinks, Obsidian optionality, source-of-truth boundaries, derived retrieval state, qmd guidance, PostgreSQL/pgvector, graph expansion, provenance, privacy, and incremental invalidation.
- [ ] Accepted app independence, canonical Markdown, no duplicate ticket model, and the separate `sync-project` defect remain literal non-regressions.
- [ ] The report ends with bounded inputs for OHR-03 and architecture candidates for OHR-02/OHR-04, without selecting adoption tier, wiki root, source-copy policy, privacy policy, provider, or success threshold.
- [ ] The parent wayfinder is published with reciprocal OHR-01/OHR-02 child links and records OHR-02's delivery-only dependency without changing the conceptual evidence frontier.
- [ ] The durable report has its own Artifact Graph section, uses `Role: research`, and points back to this ticket.

## Frontier

Ready. OHR-02 is delivery-blocked only until this ticket publishes the shared parent map; OHR-03 remains human-owned after both evidence tickets complete.

## Step-by-Step Implementation Plan

1. Read all three notes and compute source identities without modifying or copying them.
2. Inspect the accepted `llm-wiki` decisions, current skill/layout, retrieval guidance, and relevant ingest/query seams.
3. Normalize claims into the compatibility matrix with exact evidence and uncertainty.
4. Write the durable research report and publish the parent map already prepared by `to-tickets`.
5. Validate links, Artifact Graph identity, secret absence, source non-mutation, and repository lint/tests relevant to documentation.

## Testing Plan

Verify pre/post source digests; validate every cited local and repository path; run Artifact Graph audit and llm-wiki lint/tests; check that no source-note bytes, embeddings, indexes, query logs, database state, provider calls, or durable wiki mutations were created.

## Out of Scope

- Copying, moving, editing, ingesting, or compiling the three source notes.
- Building or selecting a retrieval adapter, embedding provider, database, graph algorithm, or wiki root.
- Fixing `sync_project.py`, changing app-independence, or applying a real status/merge/wiki/Pi authority.
