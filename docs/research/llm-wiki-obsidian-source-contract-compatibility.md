# Obsidian source-to-contract compatibility

## Artifact Graph

- Artifact ID: `artifact:llm-wiki-obsidian-source-contract-compatibility`
- Role: `research`
- Parent: [Obsidian-First LLM Wiki with Measured Hybrid Retrieval](../specs/llm-wiki-obsidian-hybrid-retrieval-wayfinder.md)

Produced by [OHR-01 — Research source-to-contract compatibility](../tickets/llm-wiki-obsidian-hybrid-retrieval/done/01-research-source-to-contract-compatibility.md). The ownership edge remains on the parent map because the activated ticket source is digest-bound; OHR-01's `## Produces` link supplies the reciprocal human-readable ticket edge without mutating active ticket bytes.

## Research question

Which claims in the three local Obsidian/RAG notes can the current `llm-wiki` contract reuse without weakening application independence, and which claims must remain prototype inputs or human decisions before OHR-03?

## Answer

The immediately reusable substrate is narrower than the source implementation: plain Markdown, flat YAML front matter, explicit `[[wikilinks]]`, ordinary filesystem access, source identity, provenance, audit, and Git-backed review where Git is already in use. Obsidian can author and visualize those files, but remains optional. The source-of-truth boundary stays literal: the current wiki's Markdown, indexes, provenance, timeline, audit history, and lint result remain canonical; every search index, embedding, graph score, and query cache remains derived and removable.

The PostgreSQL/pgvector pipeline, qmd, graph expansion, centrality, reranking, HTTP, MCP, and model-directed multi-hop behavior are evidence or candidates, not selected architecture. The supplied notes report a working implementation elsewhere, but that implementation's vault and repository were not supplied, so its counts, code paths, runtime status, ACL behavior, and performance are not independently observed here. OHR-03 must still choose the wiki root, source handling, adoption tier, privacy boundary, provider/model policy, and success threshold.

## Evidence boundary and source identity

Digests below are SHA-256 over each file's exact bytes, not `llm-wiki`'s universal-newline text digest. The files were read in place and were not copied, moved, edited, ingested, or compiled.

| Key | Exact local source | Bytes / lines | Exact byte SHA-256 | Observed scope |
|---|---|---:|---|---|
| S1 | `/Users/carlogiuseppesergi/Downloads/come-usiamo-obsidian.md` | 10,510 / 129 | `eecbb8aa6a187a68e2afaeea381c6a53cc80c3b5e9a0d98b01996de8b7b64b6f` | Case-study narrative. It distinguishes reported-active batch behavior from planned Git governance and a configured-but-unused REST path. The underlying vault and application repository were not supplied. |
| S2 | `/Users/carlogiuseppesergi/Downloads/obsidian-rag-ibrido-tecnologia.md` | 15,493 / 128 | `b4faac15f70ac9a0f96b040518fa5abea68810bdbf2d9792bcda2a9111b7c62c` | General technical guidance, explicitly not a statement of current project behavior. It proposes vector, fusion, reranking, and graph techniques without benchmark evidence for this corpus. |
| S3 | `/Users/carlogiuseppesergi/Downloads/obsidian-implementazione-tecnica.md` | 13,070 / 278 | `6f03b0e2867e60a0ab07aadda264f85ef5c13a3eac947e2b67e971d8ad25b9ff` | Implementation report with code and schema excerpts from another project. Referenced files, database, container, model cache, and runtime were not available for independent inspection. |

### Citation keys

Local-source citations are heading-level because these mutable files have no durable line-addressed publication:

- **S1** — `come-usiamo-obsidian.md`, especially §§ “La struttura del vault”, “Il frontmatter”, “I wikilink”, “Il plugin Local REST API”, “Dal file alla risposta”, “Git”, and “Riepilogo”.
- **S2** — `obsidian-rag-ibrido-tecnologia.md`, especially §§ “Il problema di fondo”, “Come funziona la ricerca vettoriale”, “Perché Obsidian”, “L'alternativa leggera”, “Le leve concrete”, and “Riepilogo”.
- **S3** — `obsidian-implementazione-tecnica.md`, especially §§ 1–8 and “Stato finale”.

Repository citations were inspected at OHR frontier commit `78c3c78def0335529ba8099b75becd77b32a999c`:

- **C1** — [`docs/specs/llm-wiki-app-independence-decision.md`](../specs/llm-wiki-app-independence-decision.md), §§ “Decision”, “Semantic invariants”, and “Rejected alternatives”.
- **C2** — [`llm-wiki/SKILL.md`](../../llm-wiki/SKILL.md), §§ “Core idea”, “Core principles”, “The five operations”, and “Project history”.
- **C3** — [`llm-wiki/references/tooling-tips.md`](../../llm-wiki/references/tooling-tips.md), §§ “Obsidian setup” and “Semantic search for a large wiki”.
- **C4** — [`llm-wiki/scripts/ingest_docs.py`](../../llm-wiki/scripts/ingest_docs.py), `source_digest`, `_ticket_envelope`, `classify`, `render_page`, `plan`, and `ingest`.
- **C5** — [`llm-wiki/scripts/lint_wiki.py`](../../llm-wiki/scripts/lint_wiki.py), `extract_wikilinks`, `parse_frontmatter`, `check_links`, and `check_index_drift`.
- **C6** — [`llm-wiki/scripts/sync_project.py`](../../llm-wiki/scripts/sync_project.py), `_assert_compatible`, `_assert_generated_scope`, `_source_state`, `_source_checkout`, and `sync_project`.
- **C7** — [`knowledge/purpose.md`](../../knowledge/purpose.md), §§ “Scope” and “Thesis”; [`knowledge/schema.md`](../../knowledge/schema.md), §§ “Frontmatter”, “Cross-referencing Rules”, and “Contradiction Handling”; [`knowledge/llm-wiki-project.json`](../../knowledge/llm-wiki-project.json).
- **C8** — [parent wayfinder](../specs/llm-wiki-obsidian-hybrid-retrieval-wayfinder.md), §§ “Decisions So Far”, “Unknowns and Assumptions”, “Not Yet Specified”, and “Out of Scope”.
- **C9** — [OHR-01 ticket](../tickets/llm-wiki-obsidian-hybrid-retrieval/done/01-research-source-to-contract-compatibility.md), §§ “Acceptance Criteria”, “Testing Plan”, and “Out of Scope”; [OHR-02 ticket](../tickets/llm-wiki-obsidian-hybrid-retrieval/02-benchmark-disposable-hybrid-retrieval.md), §§ “Acceptance Criteria”, “Testing Plan”, and “Out of Scope”.

External primary anchors, checked on 2026-09-01, establish product capability but do not prove the source project's use of it:

- **E1** — Obsidian Help commit [`a3985b5`](https://github.com/obsidianmd/obsidian-help/tree/a3985b585904ddb9f109bd80849b378085308c15): “How Obsidian stores data” lines 10–12, “Internal links” lines 23–42, “Properties” lines 71 and 136, and “Graph view” lines 3–10.
- **E2** — Local REST API commit [`209eff0`](https://github.com/coddingtonbear/obsidian-local-rest-api/tree/209eff08154374bbec02142ab8e763e68fb0d13b): README lines 40–87. It documents authenticated HTTPS on `127.0.0.1:27124`, CRUD, and MCP capability.
- **E3** — qmd commit [`dbfd0b4`](https://github.com/tobi/qmd/tree/dbfd0b4736aeaf761d1a16ca8e424f071df8feb9), package version `2.8.3`: README lines 5–56, 540–564, and 1129–1140. It documents npm/Bun installation, BM25 plus vector plus reranking, three first-use auto-downloaded GGUF models, and its SQLite index/cache tables.

## Existing-wiki query check

The project already has a compatible wiki root, so its `purpose.md`, `schema.md`, `wiki/index.md`, the app-independence source page, and that page's parent link were queried as compiled context. The wiki confirms the accepted app-independence and stable-identity pointers, but `knowledge/purpose.md` explicitly excludes the local Downloads notes and retrieval services. It therefore cannot answer the source-specific question. No query page or log entry was persisted because OHR-01 forbids durable wiki mutation; primary repository artifacts and the three notes provide the evidence below. [C7]

## Compatibility matrix

Status meanings are exact:

- `reuse-now` — already inside the accepted contract or usable without a new runtime dependency.
- `compatible-candidate` — does not inherently violate the contract, but needs bounded evidence and a later decision/spec.
- `contradiction` — would violate an accepted invariant or conflicts with current primary documentation as stated.
- `unobserved` — asserted by a note but not independently established from the supplied artifacts.
- `human-decision-required` — OHR-03 must authorize policy, location, dependency, or success criteria.

| Topic / claim | Status | Compatibility finding | Evidence |
|---|---|---|---|
| Markdown files are the durable corpus | `reuse-now` | The current layout and official Obsidian behavior both use filesystem Markdown. Obsidian is not needed to read, write, lint, or compile it. | S1 §§ “Cos'è Obsidian”, “Dal file alla risposta”; S3 §1; C1 D1; C2 “Core idea”; E1 “How Obsidian stores data” lines 10–12. |
| Flat YAML front matter is machine-readable metadata | `reuse-now` | The current schema already requires flat scalar/list front matter. Domain fields such as owner or classification can be source data, but current code does not thereby acquire domain validation or ACL semantics. | S1 §“Il frontmatter”; S3 §4.1; C2 “One layout”; C7 `schema.md` §“Frontmatter”; E1 “Properties” lines 71, 136. |
| Make the source implementation's required fields the global wiki schema | `human-decision-required` | `tipo`, `versione`, `classificazione`, `contiene_pii`, and tenant policy belong to the external case study. Adopting required fields or rejection behavior would be a schema and privacy decision, not direct reuse. | S1 §“Il frontmatter”; S3 §§3, 4.1; C7 `schema.md` §“Frontmatter”; C8 “Unknowns”. |
| Explicit wikilinks are durable graph edges | `reuse-now` | The skill and lint already parse and validate explicit wikilinks. They may be used as traceable edges without inferred relationships or Obsidian runtime state. | S1 §“I wikilink”; S2 §“Perché Obsidian”; C2 “Core idea”; C5 `extract_wikilinks` and `check_links`; E1 “Internal links” lines 23–42. |
| Obsidian is an optional editor and graph browser | `reuse-now` | This is a compatibility property. Official Graph view can visualize links, but compilation and ordinary navigation remain filesystem-only. | S1 §§“Cos'è Obsidian”, “I wikilink”; C1 D1; C3 §“Obsidian setup”; E1 “Graph view” lines 3–10. |
| Obsidian, `.llm-wiki/`, a plugin, HTTP, or MCP is required at runtime | `contradiction` | D1 expressly forbids application, private-state, HTTP, and MCP runtime inputs. Plugin capability does not authorize dependency. | S1 §“Il plugin Local REST API”; S3 §2; C1 D1 and rejected alternatives; E2 README lines 40–87. |
| The source project's Local REST API is active in its automatic path | `unobserved` | Both implementation notes say it is configured and manually checked but unused by code. The plugin can expose HTTPS/MCP, but no supplied runtime proves this project's configuration or use. It must not be labeled active. | S1 §“Il plugin Local REST API”; S3 §2 and “Stato finale”; E2 README lines 40–87. |
| Canonical wiki state is Markdown, provenance, timeline, audit, index, and lint | `reuse-now` | These are the accepted durable outputs. Git history may complement them but does not replace the human-to-agent `audit/` channel. | S1 §“Git”; C1 D2 and semantic invariants; C2 “Audit is the human feedback surface”; C7 `schema.md` §“Contradiction Handling”. |
| Git history alone replaces audit/provenance | `contradiction` | The source note presents Git governance as planned and not exercised; the accepted contract separately preserves correction resolution and provenance. | S1 §“Git”; S3 “Stato finale”; C1 D2 and rejected “Correct by hand-editing”; C7 `schema.md`. |
| Stable identity and source digest drive project-doc updates | `reuse-now` | Current ingest parses tickets through the canonical Ticket Envelope parser, gives Artifact IDs stable identity, and detects moved/changed/missing artifacts before rendering source pages. | C4 `_ticket_envelope`, `classify`, `plan`, `ingest`; C7 `schema.md` §“Frontmatter”. |
| The exact byte digest in this report can silently become the wiki digest | `human-decision-required` | This report hashes raw bytes. `ingest_docs.source_digest` hashes universal-newline UTF-8 text. A future external-source contract must name whether it records byte identity, normalized text identity, or both. | Source identity table; C4 `source_digest`; C8 “Source handling”. |
| The Downloads paths are current `sync-project` sources | `contradiction` | The binding includes only repository `docs/` globs, and `sync_project._source_state` expands them beneath the bound project root. The project wiki purpose explicitly excludes Downloads. | C6 `_source_state`; C7 `purpose.md` §“Scope” and `llm-wiki-project.json`. |
| Copy, pointer, move, or another durable source location | `human-decision-required` | OHR-01 may read only. OHR-03 must choose a wiki root and source-copy policy before any ingest or provenance contract can be applied. | C2 “Raw file policy”; C8 “Unknowns”; C9 OHR-01 “Out of Scope”. |
| Embeddings, lexical indexes, graph scores, and query caches are derived | `reuse-now` | They may be absent or rebuilt without changing canonical pages. No current ingest, audit, lint, or Markdown query behavior may depend on them. | S1 §“Dal file alla risposta”; S3 §§3–5; C1 D1; C3 §“Semantic search”; C8 “Decisions So Far”. |
| qmd is an optional retrieval candidate | `compatible-candidate` | A replaceable adapter could use it without making its index canonical. It is not integrated, benchmarked, or part of the current skill contract. | C3 §“Semantic search”; C8 “Reuse Map”; E3 README lines 5–56. |
| The current `pip install qmd` recipe is valid for the cited qmd project | `contradiction` | Current qmd primary documentation installs `@tobilu/qmd` through npm/Bun and requires Node 22; the repository guidance says `pip install qmd`. The recipe must not be used as executable evidence. | C3 lines 64–74; E3 README lines 32–34 and package `engines`. |
| qmd can be silently activated for OHR-02 | `contradiction` | qmd 2.8.3 auto-downloads roughly 2 GB of GGUF models on first use and persists model/index/cache state. OHR-02 forbids silent dependency/model downloads and requires disposable state. | E3 README lines 540–564 and 1129–1140; C8 “Safe working assumptions”; C9 OHR-02 “Acceptance Criteria” and “Out of Scope”. |
| PostgreSQL/pgvector is the selected store | `human-decision-required` | The source schema is useful design evidence, but adopting a database creates migration, service, ACL, deletion, and operations obligations. No accepted decision selects it. | S3 §§3–5; S1 §“Dal file alla risposta”; C8 “Not Yet Specified” and “Out of Scope”. |
| The reported pgvector/HNSW/bge-m3 pipeline is running as described | `unobserved` | The note contains internally coherent schema/code excerpts, but the referenced project, database, model, migrations, and runtime were not supplied. No performance or active-state claim is independently verified. | S3 §§3–8; S1 “Riepilogo”. |
| Deterministic direct and lexical retrieval | `compatible-candidate` | Direct title/path/heading lookup and a precisely named lexical method can be benchmarked in disposable state without changing the wiki contract. Sparse lexical vectors must not be called semantic embeddings. | S2 §§“Il problema di fondo”, “RRF”; C8 “Retrieve first, expand later”. |
| Semantic vector retrieval | `compatible-candidate` | A local semantic baseline is admissible only when its exact model, version, dimensions, cache provenance, network behavior, and cleanup are explicit. Absence of an already available model must be reported rather than hidden by a download. | S2 §“Come funziona la ricerca vettoriale”; S3 §4.3; C8 “Not Yet Specified”; E3 README lines 540–564. |
| One-hop expansion over explicit links | `compatible-candidate` | Bounded one-hop expansion is consistent with explicit-edge priority and is suitable for OHR-02 comparison after baseline retrieval. It is not current query behavior. | S2 §§“L'alternativa leggera”, “Espansione automatica”; C5 `extract_wikilinks`; C8 “Safe working assumptions”. |
| Model-directed repeated hops are active now | `unobserved` | S1 says a response model can decide to follow a link, but the current `llm-wiki` query contract only directs the agent to read selected pages and one link level; there is no supported retrieval adapter or observed automatic multi-hop implementation. | S1 §“I wikilink”; S2 §“L'alternativa leggera”; C2 `query` steps; C8 “Not Yet Specified”. |
| Centrality, PageRank, communities, HyDE, cross-encoder reranking, or inferred edges | `compatible-candidate` | These remain separately measurable options. None has earned production complexity, and inferred edges would need explicit provenance, confidence, and removal semantics. | S2 §§“Le leve concrete”, “Riepilogo”; C8 “Decisions So Far” and “Not Yet Specified”. |
| Reported scale and quality gains | `unobserved` | Claims such as a practical note-count range, typical reranking gain, or graph superiority have no corpus-specific benchmark in the supplied evidence. OHR-02 must measure rather than inherit them. | S2 §§“L'alternativa leggera”, “Reranking”, “Riepilogo”; C8 “Question set and success threshold”. |
| Source provenance survives retrieval | `compatible-candidate` | Current pages carry source path, digest, status, identity, and dates. A retriever may return those identifiers, but chunk identity, model/index provenance, and citation-to-source mapping are not specified. | S1 §“Dal file alla risposta”; S3 §§3, 5, 6; C4 `render_page`; C7 `schema.md`; C8 “Not Yet Specified”. |
| Tenant/classification filters make a future index private-safe | `unobserved` | The notes report ACL filtering and bugs in another system. The current wiki has no tenant authorization contract, and local vectors/query logs can retain sensitive content. | S1 §§“Il frontmatter”, “Riepilogo”; S3 §§3, 5, 7.1; C7 `purpose.md` §“Out of scope”; C8 “Privacy boundary”. |
| Privacy, retention, deletion, and query logging policy | `human-decision-required` | OHR-03 must decide allowed source classes, index location, access boundary, logs, deletion, redaction, and whether any provider may receive text before production work. | S1 §“Il frontmatter”; S3 §§3–6; C8 “Privacy boundary”. |
| Source-hash incremental ingest | `compatible-candidate` | The source implementation's registry pattern aligns with current changed/moved/missing source detection, but only at different boundaries and with different identities. | S1 §“Dal file alla risposta”; S3 §4.4; C4 `plan` and `ingest`. |
| Incremental invalidation is already complete from changed source through retrieval | `contradiction` | Current code updates compiled source pages and timelines; it has no chunk, embedding, graph, or persisted-answer invalidation contract. Updating only the changed note is insufficient if neighbors or cached answers include its content. | S2 §“Aggiornamento incrementale”; S3 §4.4; C4 `plan`; C6 `sync_project`; C8 “Not Yet Specified”. |
| Reprocess changed note plus backlinks | `compatible-candidate` | This is a bounded candidate for graph-derived context, not a proven universal rule. Exact invalidation depends on chunking, expansion, persisted answers, and removal behavior. | S2 §“Aggiornamento incrementale”; C8 “Not Yet Specified”. |
| A second ticket/status model is introduced for wiki work | `contradiction` | `ingest_docs` delegates ticket parsing to Ticket Autopilot and derives stable `ticket:<folder>/<id>` identities. Both focused-spec and wayfinder paths must keep Ticket Envelope v1. | C4 `_ticket_envelope` and `classify`; C8 “No duplicate ticket model”. |
| Retrieval work fixes or absorbs the existing `sync-project` defect | `contradiction` | Discovery/binding/publication remain their own fail-closed boundary. This initiative records no defect diagnosis, fix, or authority for it. | C6 `_assert_compatible`, `_source_checkout`, `sync_project`; C8 “The existing `llm-wiki sync-project` defect is separate”. |
| Adoption tier, root, source policy, provider/model, and threshold are implied by this report | `human-decision-required` | Evidence does not grant production architecture authority. OHR-03 remains HITL after OHR-01 and OHR-02. | C8 “Unknowns”, “Frontier”, and “Ticket Plan”. |

## Non-regression contract

Any later spec must preserve these literal boundaries:

1. **Application independence:** no application, `.llm-wiki/` state, Local REST API, HTTP API, or MCP server is required for ingest, compile, audit, lint, or Markdown navigation. [C1]
2. **Canonical Markdown:** generated retrieval state is rebuildable and never outranks source pages, source identity, provenance, timeline, audit, index, or lint evidence. [C2, C4, C7]
3. **One ticket model:** wiki lifecycle pages compile canonical Ticket Envelope v1 and repository lifecycle evidence; they do not create parallel ticket state. [C4, C8]
4. **Separate sync defect:** OHR work neither diagnoses nor fixes the existing `sync-project` defect and does not reinterpret a broken binding as retrieval evidence. [C6, C8]
5. **No implied authorities:** research, benchmark results, provider observation, wiki mutation, delivery, merge, and local Pi synchronization remain separate. [C8]

## Bounded candidate inputs

### OHR-02 benchmark candidates

These are candidates, not a selected benchmark implementation:

- direct filename/title/heading lookup;
- a precisely named deterministic lexical baseline, such as token-overlap or BM25 where the available standard-library/runtime seam is recorded;
- a precisely named sparse TF-IDF cosine baseline labeled **lexical vector**, never semantic embedding;
- a semantic vector baseline only if an exact pre-existing local model and cache can be proven without installation, download, network, or durable state; otherwise record it as unavailable;
- rank fusion with its exact formula and inputs, independently of score scales;
- at most one-hop expansion over explicit `[[wikilinks]]`, with the seed result and expanded source traceable separately;
- per-question relevance, citation/path correctness, latency, build/update cost, result-set delta, and cleanup evidence.

qmd may be an observed candidate only if its dependency and all required models are already present and the run can redirect and delete every index/cache. OHR-02 must not execute the current `pip install qmd` recipe, auto-download qmd's models, call a provider, persist a wiki query, or describe sparse lexical vectors as semantic. [C3, E3]

### OHR-04 architecture candidates

OHR-03 may later choose among, reject, or refine:

- content-only: no supported retrieval component;
- corrected documentation for an optional external command, still outside the skill contract;
- a replaceable local adapter with explicit derived-state, rebuild, invalidation, and cleanup contracts;
- a service-backed adapter such as PostgreSQL/pgvector with explicit migration, authorization, retention, deletion, and operations ownership;
- a graph projection limited to explicit links/metadata, with inferred edges separately marked and removable;
- separate source ingest and retrieval integration specs, candidates, runs, and publication evidence.

## Required OHR-03 decisions

OHR-03 must explicitly record all of the following; silence is not adoption:

1. chosen wiki root and owner;
2. copy, pointer, move, or other source-handling policy for each local note;
3. raw-byte versus normalized-text digest convention, and whether both are retained;
4. content-only, documented recipe, supported local adapter, service-backed integration, or no-build tier;
5. question fixture and numerical/ordinal success threshold;
6. source classification, embedding/index location, access control, query-log, retention, deletion, and redaction policy;
7. allowed dependency, provider, model, model-cache, download, offline, and reproducibility policy;
8. direct/lexical/vector/fusion/graph scope and the maximum expansion depth;
9. chunk, citation, derived-state provenance, and complete invalidation semantics;
10. whether any new decision spec amends app independence; absent an explicit amendment, C1 remains authoritative.

## Verification and non-mutation evidence

- The report contract check passed: one Artifact Graph, all five matrix statuses and required topics present, 14 repository-relative links resolved, and all three exact source digests matched.
- The canonical Artifact Graph audit remained at 26 known repository errors before and after (`148 → 149` nodes, `28 → 28` warnings, `36 → 36` unreferenced); no OHR path has an audit error.
- All 165 `llm-wiki` unit tests and all 24 focused Artifact Graph tests passed.
- Direct lint of the existing bound `knowledge/` wiki ran and honestly remained red at its pre-existing baseline: 14 errors, 215 warnings, and 15 informational findings, including stale/dangling compiled sources. This candidate did not mutate that wiki or claim to fix its separate sync boundary.
- The three source files had identical exact-byte SHA-256 values before and after research: S1 `eecbb8aa…b64b6f`, S2 `b4faac15…7c62c`, S3 `6f03b0e2…25b9ff`.
- No source was copied under `raw/`, `wiki/`, `knowledge/`, or repository docs.
- The existing project wiki was read only. No `wiki/queries/` page, log entry, index update, source page, or audit record was created.
- No embedding model, database, index, query cache, HTTP/MCP integration, or provider-backed retrieval call was created for this research.
- No secret value was read or recorded; source references to API keys remain capability/configuration claims only.
- The committed parent map already contains reciprocal OHR-01/OHR-02 child links and describes OHR-02's dependency as repository-delivery ordering, not conceptual evidence dependence. [C8]

## Unknowns

- The external case-study repository and live vault were not supplied, so their reported state remains unobserved.
- No corpus-specific retrieval benchmark exists yet; OHR-02 owns that evidence.
- No selected wiki root or permission to preserve the three sources exists.
- No production dependency, model, provider, index, graph algorithm, or success threshold has been authorized.

## Next step

Run OHR-02 only in disposable state against the exact source digests above. Then present OHR-01 and OHR-02 together to the human-owned OHR-03 decision. Do not emit OHR-04/OHR-05 production tickets or mutate a durable wiki before that decision.
