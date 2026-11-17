# OHR-03 — Adoption tier for optional LLM Wiki retrieval

## Artifact Graph

- Artifact ID: `artifact:llm-wiki-local-retrieval-adoption-decision`
- Role: `spec`
- Parent: [Obsidian-First LLM Wiki with Measured Hybrid Retrieval](llm-wiki-obsidian-hybrid-retrieval-wayfinder.md)

The feature that implements this decision is specified in
[OHR-04 — `wiki-rag` local retrieval adapter](wiki-rag-local-adapter.md).

## Type

Decision spec. Human decision recorded on 2026-11-17 by the repository owner, in chat.

## Gates

- attempt: recording this decision and its OHR-04 spec through handoff;
- budget, time and maximum attempts: none set;
- approvals: the decision fields below were given by the owner; merge of the delivering PR is `open`;
- exact version: none named by the owner (QMD `2.8.3` is the version measured, see OHR-04);
- existing blocks: `llm-wiki-app-independence-decision.md` (checked below; not violated);
  `scripts/file-limits.json` (does not list new skills; `llm-wiki/SKILL.md` is not capped).

## Evidence that closes the OHR-02 gap

OHR-02 could not measure a semantic method: no embedding model existed inside its boundary.
A project-bound wiki outside this repository (an operational on-call wiki of 64 pages, kept
private) has since run a local QMD 2.8.3 adapter with real GGUF embeddings. Observations on
that machine on 2026-11-17, one run each, not a benchmark:

| Route | Question | Top result | Time |
|---|---|---|---|
| exact text search | a provider error code | the right glossary row | instant |
| `vector` (CPU) | a natural-language question about refunds | the right glossary page, rank 1 | 5 s |
| `query` hybrid (CPU forced) | the error code | no answer; stopped after >7 min, ~3.8 GB RAM | — |
| `query` hybrid (GPU, Vulkan, 4 GB VRAM) | the error code | glossary, rank 1 | 74.8 s incl. model load |
| `query` hybrid (GPU) | the refund question | glossary, rank 1 | 32.7 s |

Peak VRAM during the GPU runs was 2.76 GB. An earlier gate run on the same adapter recorded
7.41 s vector and 594.79 s hybrid on CPU. Identifiers were found reliably only by exact text:
embeddings put near-identical codes close together.

## Decision

| OHR-03 field | Decision |
|---|---|
| Adoption tier | **Supported local retrieval adapter**, shipped inside `llm-wiki` as `rag/` (scaffold script and templates) with `references/wiki-rag.md`. It scaffolds the adapter into a project. Not a service, not a runtime dependency of `llm-wiki`. |
| Default device | `auto`: QMD/node-llama-cpp choose Metal on Apple Silicon, then CUDA, Vulkan, then CPU. `cpu` stays available. Auto **must work on Apple Metal**. |
| Retrieval routes | Exact text search for identifiers and codes; `vector` for natural-language questions; hybrid `query` only on explicit request. A lexical `search` (BM25) route is also exposed. |
| Success threshold | On a fixed question set, `vector` returns the expected page in the top 3 for at least 8 of 10 questions, under 10 s on CPU. For codes and identifiers only exact search counts. |
| Privacy boundary | Corpus = the wiki's Markdown only. Indexes, models and caches stay in a project-local ignored state directory. Network only during the explicit `models`/`prepare` maintenance command (model download); queries never touch the network. |
| App independence | **No amendment.** The adapter does not read `.llm-wiki/`, the third-party application, or its HTTP/MCP surfaces; the wiki stays fully usable with no index. |
| Wiki root and source-copy policy for the three Obsidian notes | **Not decided.** OHR-05 stays blocked on these two fields. |

## Consequences

- `llm-wiki` keeps Markdown canonical; its `query` operation gains the route order above and
  points to `references/wiki-rag.md` for the supported adapter, still probing availability without installing.
- `llm-wiki/references/tooling-tips.md` loses its incorrect `pip install qmd` recipe (QMD is the
  npm package `@tobilu/qmd`).
- `research` and `ask-skills` need no change: both already delegate to `llm-wiki query` and its
  availability contract.

## Amendment (2026-11-17, same day)

The first delivery shipped the adapter as a separate skill `wiki-rag`. CI rejected it: every
installed skill adds its description to the always-on listing, and the controlled context budget
had a 6-byte margin (`ticket-autopilot/references/token-reduction-guide` explains why exceeding it
is a decision). The owner chose to move the scaffolder inside `llm-wiki` rather than raise the
ceiling or shorten other descriptions. The adapter has no runtime coupling to `llm-wiki`: the skill
only points to it, and its Node files run only in the project that scaffolds them.

## Alternatives considered

- Documented optional recipe only: cheapest, but leaves every project to rebuild the
  canonical-result checks, stale-index detection and fallback that the measured adapter has.
- Service-backed integration (PostgreSQL/pgvector, HTTP, MCP): rejected for now; no measurement
  justifies a resident service, and it conflicts with the no-persistent-process boundary.
- Making the adapter a runtime part of `llm-wiki`: rejected; `llm-wiki` must keep working with
  CPython and the filesystem alone. Shipping the scaffolder files inside it does not change that.
