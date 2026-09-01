# Obsidian-First LLM Wiki with Measured Hybrid Retrieval

## Artifact Graph

- Artifact ID: `artifact:llm-wiki-obsidian-hybrid-retrieval-wayfinder`
- Role: `wayfinder`
- Standalone: true

### Children

- [OHR-01 — Research source-to-contract compatibility](../tickets/llm-wiki-obsidian-hybrid-retrieval/done/01-research-source-to-contract-compatibility.md)
- [OHR-02 — Benchmark disposable hybrid retrieval](../tickets/llm-wiki-obsidian-hybrid-retrieval/done/02-benchmark-disposable-hybrid-retrieval.md)
- [OHR-01 source-to-contract compatibility report](../research/llm-wiki-obsidian-source-contract-compatibility.md)
- [OHR-02 disposable hybrid-retrieval benchmark](../research/llm-wiki-obsidian-retrieval-benchmark.md)

## Type

Wayfinding spec

## Status

**Initial evidence frontier assembled.** OHR-01 is completed and its report is delivered.
OHR-02 remains conceptually independent evidence; its disposable benchmark candidate is linked
here after the OHR-01 delivery-order dependency was satisfied. OHR-03 remains human-owned and
cannot begin until the OHR-02 report is also integrated. The evidence preserves the accepted
app-independence boundary and measures retrieval value without choosing an implementation.

## Source Bundle

This map was prompted by three local Markdown notes:

- `/Users/carlogiuseppesergi/Downloads/come-usiamo-obsidian.md`
- `/Users/carlogiuseppesergi/Downloads/obsidian-rag-ibrido-tecnologia.md`
- `/Users/carlogiuseppesergi/Downloads/obsidian-implementazione-tecnica.md`

They are evidence for this investigation, not yet copied into a wiki or this repository. Their
main claims form one coherent case study:

1. Obsidian is a local-first Markdown authoring and navigation surface built around front
   matter and wikilinks.
2. The current application reads a vault without rewriting it, parses and chunks Markdown,
   creates embeddings, and stores retrieval state in PostgreSQL with pgvector. A REST API is
   configured but is not part of the observed active path.
3. The recommended evolution is incremental: establish a vector or hybrid retrieval baseline
   first, then add graph expansion or centrality only if a benchmark demonstrates a gain.

## Destination

A project-bound LLM Wiki can use an Obsidian vault as its plain-Markdown corpus and can answer
questions through an optional, replaceable retrieval layer without making either Obsidian or a
retrieval service part of the wiki's source of truth:

- the three source notes are preserved with provenance under the chosen wiki root and compiled
  into linked concept, source, comparison, and synthesis pages;
- Obsidian remains an optional editor and graph browser: front matter and `[[wikilinks]]` are
  durable Markdown data, while plugins, local databases, and HTTP services are not required;
- the wiki's Markdown pages, indexes, provenance, timeline, audit trail, and lint result remain
  canonical; embeddings, lexical indexes, centrality scores, and query caches are derived and
  rebuildable;
- a reproducible question set measures retrieval quality and latency against at least a
  non-semantic baseline and a lexical-plus-vector baseline;
- graph-aware retrieval is introduced only after a bounded prototype shows a material gain over
  that baseline, and any graph expansion uses explicit wiki links or declared metadata rather
  than silently inventing relationships;
- the retrieval adapter can be replaced or absent without changing ingest, compilation, audit,
  lint, or ordinary Markdown navigation;
- the result documents how a direct `to-spec -> to-tickets -> ticket-autopilot` initiative and a
  broader `wayfinder -> focused spec -> to-tickets -> ticket-autopilot` initiative both feed the
  same project wiki without introducing a second artifact model.

A successful destination is therefore not "put pgvector inside `llm-wiki`." It is a useful
compiled wiki plus evidence that justifies whichever optional retrieval boundary is selected.

## Decisions So Far

- **The existing app-independence decision remains authoritative.**
  [llm-wiki-app-independence-decision.md](llm-wiki-app-independence-decision.md) forbids runtime
  dependence on an application, its `.llm-wiki/` state, its HTTP API, or its MCP server. This
  initiative may amend that decision only through a new explicit decision spec; it may not
  erode it implicitly.
- **Markdown is canonical; retrieval state is a projection.** A vault must remain readable and
  operable when no index exists and no service is running.
- **Obsidian compatibility is a property, not a dependency.** The current wiki layout already
  uses flat front matter and wikilinks that Obsidian understands. Obsidian can author and browse
  the content, but the skill must continue to work with CPython and the filesystem alone.
- **The source bundle describes one implementation, not the required architecture.** Its
  PostgreSQL/pgvector store and configured REST API are inputs to comparison. They are not
  selected components.
- **Retrieve first, expand later.** Lexical/vector retrieval gets a measured baseline before
  centrality, communities, or multi-hop expansion are considered.
- **Explicit graph edges outrank inferred graph edges.** Wikilinks, source relationships, and
  Artifact Graph metadata are admissible inputs. Automatically inferred edges must be visibly
  derived, confidence-bearing, and removable.
- **No duplicate ticket model.** Wayfinder emits the same canonical Ticket Envelope v1 that a
  focused spec emits. The wiki compiles artifacts and lifecycle history from both entry paths.
- **The existing `llm-wiki sync-project` defect is separate.** Its reproduction, spec, tickets,
  and run must not be folded into this retrieval initiative.
- **Ticket Autopilot progress reporting is separate.** Percentage and ticket-state visibility
  concern runner observability, not this wiki architecture.

## Reuse Map

| Existing capability | Reuse | Gap or constraint |
|---|---|---|
| Plain Markdown layout with flat front matter and wikilinks | Direct | None for Obsidian browsing |
| `raw/sources/`, `wiki/sources/`, concepts, comparisons, synthesis | Direct | The three local notes still need an explicit target wiki and ingest pass |
| Project binding and docs/session ingest | Direct for project artifacts | External-note ingest remains agent-driven rather than a deterministic project sync |
| Provenance, stable identities, audit, and drift lint | Direct | Retrieval-derived claims need an explicit provenance convention if persisted |
| Obsidian graph view | Optional human interface | Not a query API or a runtime dependency |
| Optional `qmd` BM25-plus-vector recipe in `tooling-tips.md` | Candidate baseline | Not integrated, benchmarked, or part of the skill contract |
| PostgreSQL/pgvector pipeline described by the source bundle | Design evidence | Adds service, schema, operational, migration, and privacy costs |
| Artifact Graph edges and wiki wikilinks | Candidate graph projection | No supported query-time expansion or centrality contract exists |
| Application REST API | None yet | Configured-but-unused evidence cannot justify adopting it |

## Unknowns and Assumptions

### Must be decided before production specification

- **Wiki instance and ownership.** The earlier project-history map leaves the location and Git
  tracking of this repository's wiki instance open. This initiative needs a chosen root before
  it can perform a durable source ingest.
- **Adoption tier.** Choose among: content-only pilot; documented optional search recipe;
  supported local retrieval adapter; or a service-backed retrieval integration. Each tier has a
  different support and verification burden.
- **Question set and success threshold.** Relevance, citation correctness, latency, index build
  time, and update cost need explicit measures. "Feels better" is not an acceptance criterion.
- **Source handling.** Decide whether the three files may be copied into `raw/sources/`, must be
  represented by pointer files under `raw/refs/`, or should be moved to another durable source
  location first.
- **Privacy boundary.** Local embeddings and query logs can disclose source content even when
  the Markdown stays local. Storage, deletion, and redaction policy depend on the selected tier.

### Safe working assumptions for the first frontier

- The three files can be read during research and in a temporary prototype but will not be
  moved, edited, or copied durably before the source-handling decision.
- The current `llm-wiki` layout and accepted decisions are the baseline under test.
- A prototype may use disposable state outside the repository and selected wiki root. It cannot
  be promoted to production.
- Graph retrieval begins with one-hop expansion over explicit links. Broader expansion must earn
  its complexity independently.

## Not Yet Specified

- Retrieval adapter interface, provider, model, embedding dimension, chunking policy, and index
  persistence.
- Whether BM25/vector fusion is reciprocal-rank fusion, weighted score fusion, reranking, or an
  external tool's contract.
- How query answers cite chunks versus compiled pages, and whether durable answers are filed in
  `wiki/queries/` automatically or only after review.
- Incremental invalidation from a changed source through chunks, embeddings, graph projection,
  compiled pages, and persisted answers.
- Graph centrality/community algorithms and the evidence threshold that would justify them.
- Operational support for PostgreSQL, pgvector, a local embedded index, or MCP. None is selected.
- Installation or packaging changes. Those follow only from the adoption-tier decision.

## Out of Scope

- Making Obsidian mandatory or automating an Obsidian plugin.
- Replacing `llm-wiki`'s compiled Markdown model with retrieve-raw-on-every-query RAG.
- Treating generated embeddings, graph scores, or query caches as the authoritative wiki.
- Depending on `.llm-wiki/`, the third-party LLM Wiki application, or its REST/MCP surfaces.
- Introducing PostgreSQL/pgvector solely because the source implementation uses it.
- Implementing graph expansion without a baseline and a measured improvement.
- Fixing `sync_project.py` or combining its bug provenance with this initiative.
- Implementing Ticket Autopilot's run-progress indicator.

## Frontier / Blocking Edges

```text
OHR-01 source-to-contract research --------------------+
                                                        +--> OHR-03 adoption decision (HITL)
OHR-02 disposable retrieval benchmark ----------------+

OHR-03 adoption decision --> OHR-04 focused production spec
OHR-03 adoption decision --> OHR-05 wiki-instance ingest spec

OHR-04 focused production spec --> to-tickets --> ticket-autopilot
OHR-05 wiki-instance ingest spec --> to-tickets --> ticket-autopilot
```

`OHR-01` and `OHR-02` are the initial independent frontier. `OHR-03` is deliberately human-owned:
the benchmark may quantify trade-offs, but it cannot authorize service dependencies, persistent
indexes, source copying, or a wiki location. `OHR-04` and `OHR-05` remain separate so a useful
content wiki does not wait for an optional search integration, and so infrastructure work cannot
silently rewrite the source-ingest scope.

## Ticket Plan

Only the current frontier is emitted. OHR-02's repository-delivery dependency on OHR-01
serializes parent-map publication; it does not let OHR-01's conclusions constrain the
benchmark questions or measurements.

| ID | Type | Mode | Blocks on | Observable output |
|---|---|---|---|---|
| OHR-01 | research | AFK | — | A source-to-contract compatibility report separating immediately reusable wiki behavior, contradictions with accepted decisions, and architecture candidates |
| OHR-02 | prototype | AFK | OHR-01 (delivery ordering only) | A disposable benchmark over the three sources comparing deterministic/lexical lookup, lexical-plus-vector retrieval, and at most one-hop explicit-link expansion, with fixtures, questions, measures, and cleanup evidence |
| OHR-03 | decision | HITL | OHR-01, OHR-02 | A recorded choice of wiki root, source-copy policy, adoption tier, success threshold, privacy boundary, and whether app independence needs amendment |
| OHR-04 | feature/decision spec | AFK | OHR-03 | A focused production spec for the selected optional retrieval tier, or an explicit no-build decision if the prototype does not justify it |
| OHR-05 | feature spec | AFK | OHR-03 | A separate spec for ingesting and compiling the three notes in the chosen wiki instance, including provenance, expected pages, query checks, and lint baseline |

## Verification Strategy

The eventual production spec must turn the following into exact checks; this map does not claim
that they have run:

- The wiki remains usable, lintable, and queryable through ordinary Markdown navigation with all
  optional retrieval components absent.
- Every durable page derived from the three notes links to preserved source provenance.
- Rebuilding an optional index from unchanged Markdown is deterministic at the selected contract
  boundary, or explicitly records provider/model nondeterminism without claiming byte identity.
- Changed or removed source content cannot survive invisibly in results after an incremental
  refresh.
- The benchmark records per-question relevance/citation outcomes and latency for each baseline;
  graph expansion ships only if it crosses the threshold chosen in `OHR-03`.
- An explicit wikilink edge can be traced from source Markdown to graph projection to retrieved
  context. Inferred edges, if selected later, are distinguishable from explicit ones.
- No test, script, or document turns Obsidian, PostgreSQL, pgvector, qmd, an HTTP API, or an MCP
  server into an undeclared requirement.
- The source-ingest run and retrieval-integration run have separate specs, ticket folders,
  candidate trees, verification records, and delivery provenance.

## Next Review

Review only after both OHR reports have terminal delivery proof. Use the benchmark's explicit
Q04 failure, unavailable semantic baseline, Q10 recall/noise delta, cleanup evidence, and the
OHR-01 compatibility matrix as inputs. The review is not a free-form design session: it must
choose the `OHR-03` fields, then route the two selected outcomes into separate focused specs.
Until then, do not emit implementation tickets and do not mutate a durable wiki.
