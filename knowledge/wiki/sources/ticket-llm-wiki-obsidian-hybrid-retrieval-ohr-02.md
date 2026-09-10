---
type: source
title: "Benchmark disposable hybrid retrieval over the Obsidian notes"
identity_key: ticket:llm-wiki-obsidian-hybrid-retrieval/OHR-02
identity_strength: stable
source_path: docs/tickets/llm-wiki-obsidian-hybrid-retrieval/done/02-benchmark-disposable-hybrid-retrieval.md
source_digest: sha256:02c1414aab961201e92b29e63b07efc386e5953f278328336ab832971eeb3197
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-01
created_provenance: git-commit
disposition_changed: 2026-09-01
disposition_changed_provenance: git-rename
run_id: llm-wiki-obsidian-hybrid-retrieval-v2-20260901
---

# Benchmark disposable hybrid retrieval over the Obsidian notes

Compiled from `docs/tickets/llm-wiki-obsidian-hybrid-retrieval/done/02-benchmark-disposable-hybrid-retrieval.md`. Identity is `ticket:llm-wiki-obsidian-hybrid-retrieval/OHR-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-01** via `git-commit`
- Disposition changed: **2026-09-01** via `git-rename`

## Graph

- Parent source: [[sources/artifact-llm-wiki-obsidian-hybrid-retrieval-wayfinder]]
- Blocked by: [[sources/ticket-llm-wiki-obsidian-hybrid-retrieval-ohr-01]] — `ticket:llm-wiki-obsidian-hybrid-retrieval/OHR-01`

## Run

Completed under autopilot run `llm-wiki-obsidian-hybrid-retrieval-v2-20260901`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[5],"status":"present"},"exclusions":{"headings":[9],"status":"present"},"frontier":{"headings":[6],"status":"present"},"intent":{"headings":[4],"status":"present"},"testing":{"headings":[8],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-obsidian-hybrid-retrieval-ohr-02.md","payload_bytes":4566,"payload_sha256":"02c1414aab961201e92b29e63b07efc386e5953f278328336ab832971eeb3197"}],"payload_bytes":4566,"payload_sha256":"02c1414aab961201e92b29e63b07efc386e5953f278328336ab832971eeb3197","schema":1,"source_digest":"sha256:02c1414aab961201e92b29e63b07efc386e5953f278328336ab832971eeb3197","source_identity":"ticket:llm-wiki-obsidian-hybrid-retrieval/OHR-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 4: What to Build |
| acceptance | 5: Acceptance Criteria |
| testing | 8: Testing Plan |
| frontier | 6: Frontier |
| exclusions | 9: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4566,"payload_sha256":"02c1414aab961201e92b29e63b07efc386e5953f278328336ab832971eeb3197","schema":1,"source_digest":"sha256:02c1414aab961201e92b29e63b07efc386e5953f278328336ab832971eeb3197","source_identity":"ticket:llm-wiki-obsidian-hybrid-retrieval/OHR-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "OHR-02"
execution_mode: AFK
blocked_by:
  - "OHR-01"
---

# Benchmark disposable hybrid retrieval over the Obsidian notes

## Artifact Graph

- Artifact ID: `artifact:ohr-02-disposable-hybrid-retrieval-benchmark`
- Role: `ticket`
- Parent: [Obsidian-First LLM Wiki with Measured Hybrid Retrieval](../../specs/llm-wiki-obsidian-hybrid-retrieval-wayfinder.md)

## Parent Spec

[Obsidian-First LLM Wiki with Measured Hybrid Retrieval](../../specs/llm-wiki-obsidian-hybrid-retrieval-wayfinder.md)

## Produces

- [Disposable hybrid-retrieval benchmark report](../../research/llm-wiki-obsidian-retrieval-benchmark.md)

## What to Build

Run a throwaway, reproducible benchmark over read-only copies of the three source notes. Compare deterministic direct/lexical lookup, lexical-plus-vector fusion, and at most one-hop expansion over explicit links. Persist only the benchmark contract, aggregate results, limitations, and cleanup evidence in a research report; remove temporary chunks, indexes, vectors, caches, and query logs. The benchmark informs OHR-03 but grants no production decision.

## Acceptance Criteria

- [ ] The report records exact source paths/digests, disposable fixture location, chunking/tokenization rules, query set, relevance judgments, citation expectations, cold/warm timing method, and tool/runtime versions.
- [ ] At least eight questions cover direct facts, cross-note synthesis, terminology, implementation boundaries, privacy, incremental update behavior, and a deliberate no-answer case without deriving judgments from the systems under test.
- [ ] Baselines include deterministic direct lookup, lexical ranking, lexical-plus-vector fusion, and one-hop explicit-link expansion where a real edge exists; if the source graph has no usable edge, expansion is reported as a no-op and exercised only in a clearly separate synthetic control.
- [ ] Any vector baseline is named precisely (semantic embedding, sparse lexical vector, or other); unavailable local embedding capability is a measured limitation, never relabeled as semantic evidence and never fetched from a network silently.
- [ ] Per-question results record ranked source/chunk IDs, relevance, citation correctness, unsupported-context rate, latency, index-build time, update/removal behavior, and enough raw aggregate data to reproduce every summary.
- [ ] The report compares gain and cost without declaring a winner, production threshold, provider, database, adoption tier, source-copy policy, privacy policy, or graph algorithm.
- [ ] Source notes remain byte-identical, no durable wiki is mutated, all prototype state is outside the repository, and cleanup is proven by an explicit post-run inventory.
- [ ] The durable report has one Artifact Graph section, uses `Role: research`, and points back to this ticket.

## Frontier

Dependency-blocked by OHR-01 only for parent-map delivery ordering. The benchmark questions and judgments remain independent of OHR-01's conclusions. OHR-03 remains HITL after both reports.

## Step-by-Step Implementation Plan

1. Freeze source identities and a human-readable question/relevance fixture before running retrieval.
2. Build disposable read-only chunks and deterministic direct/lexical baselines.
3. Exercise the best locally available precisely named vector baseline without installing or downloading undeclared dependencies.
4. Measure lexical/vector fusion and bounded explicit-link expansion, including update/removal and no-answer controls.
5. Delete all temporary state, verify source digests, and write the durable benchmark report with raw aggregate tables and limitations.
6. Run report-link, Artifact Graph, llm-wiki, and repository-adjacent checks.

## Testing Plan

Use only disposable local fixtures and deterministic clocks/measurement descriptions. Rerun stable-result portions, verify rank/citation calculations from persisted aggregate rows, mutate and remove a temporary source copy to test invalidation, confirm no undeclared network/provider access, and prove cleanup plus original source digest equality.

## Out of Scope

- Promoting prototype code, chunks, vectors, indexes, caches, or query logs into production or the repository.
- Downloading an embedding model, installing a database, invoking a remote provider, or adopting PostgreSQL/pgvector, qmd, MCP, or an HTTP service.
- Choosing OHR-03's wiki root, source handling, adoption tier, threshold, privacy boundary, or app-independence amendment.
- Ingesting source notes into a durable wiki or implementing OHR-04/OHR-05.

```
