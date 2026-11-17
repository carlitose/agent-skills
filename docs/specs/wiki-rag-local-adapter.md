# OHR-04 — `wiki-rag`: local retrieval adapter for an LLM Wiki

## Artifact Graph

- Artifact ID: `artifact:wiki-rag-local-adapter`
- Role: `spec`
- Parent: [Obsidian-First LLM Wiki with Measured Hybrid Retrieval](llm-wiki-obsidian-hybrid-retrieval-wayfinder.md)

Decided by [OHR-03 — Adoption tier](llm-wiki-local-retrieval-adoption-decision.md).

## Type

Feature spec.

## Gates

- attempt: the `wiki-rag` skill, the `llm-wiki` updates and their tests, through handoff;
- budget, time and maximum attempts: none set;
- approvals: merge of the delivering PR is `open`; no publication, install or reload of the
  local Pi package is authorized by this spec;
- exact version: QMD `@tobilu/qmd` pinned to `2.8.3`, the measured version; Node `>=22`;
- existing blocks: `scripts/file-limits.json` caps listed `SKILL.md` files and a 1300-line total;
  the new skill must stay short. CI (`local-profile.yml`) runs lint and the local profile; it
  installs no npm packages for skills, so tests must not need `node_modules` or models.

## Goal

A project with an `llm-wiki` wiki can add optional local retrieval with one scaffold command,
and agents choose the right retrieval route for the question.

## Non-goals

- Changing `llm-wiki`'s compiled-Markdown model or making retrieval required.
- Any resident service, MCP server, database server, hook, auto-sync or scheduled reindex.
- Indexing anything other than the wiki's Markdown pages (no raw sources, sessions, mail).
- Graph expansion or centrality.
- OHR-05 (ingesting the three Obsidian notes).

## Target behavior

### The `wiki-rag` skill

`wiki-rag/SKILL.md` explains when to use it (a project wants local semantic search over its
LLM Wiki) and how; `wiki-rag/scripts/scaffold.mjs` does the work:

```bash
node <skill>/scripts/scaffold.mjs <project-root> --name <name> --wiki <relative-wiki-dir> [--device auto|cpu]
```

It writes into the project, refusing to overwrite existing files:

- `tools/<name>-rag/` — `rag.mjs`, `contract.mjs`, `hybrid.mjs`, `package.json` (QMD pinned),
  `rag.config.json` (`schema`, `name`, `wiki`, `device`) and a short README;
- `skills/<name>-rag/SKILL.md` — the project contract naming adapter `qmd-local-v1` and
  binding `<name>-wiki-local-v1`, with the route order below;
- `tests/<name>-rag.Tests.mjs` — the adapter's pure tests;
- `.gitignore` lines for `/.<name>-rag/` and `/tools/<name>-rag/node_modules/` (appended once).

It never runs `npm`, downloads models or builds an index; it prints those next commands.

### The scaffolded adapter

Commands, run as `node tools/<name>-rag/rag.mjs <command>`:

| Command | Behavior | Network |
|---|---|---|
| `status` | Read-only probe: mode `rag/hybrid:qmd-local-v1` or `compiled-markdown` with a concrete reason | none |
| `models` | Downloads the three pinned GGUF models into the state dir | yes (explicit) |
| `prepare` | Indexes and embeds the wiki; writes the manifest | only if models are missing |
| `search <words>` | BM25 lexical route | none |
| `vector <question>` | Embedding route | none |
| `query <question>` | Hybrid: expansion + BM25 + vector + RRF + reranker, via the QMD CLI | none |

Kept from the measured adapter: canonical-page check with citation and SHA-256 for every hit;
stale/missing/incomplete index, changed model or changed CLI config fall back to
`compiled-markdown` with a reason; no download or install from `status` or a query.

Device: `rag.config.json.device` is `auto` by default. `auto` leaves `QMD_FORCE_CPU` unset so
QMD/node-llama-cpp select Metal on Apple Silicon, then CUDA, Vulkan, then CPU, falling back to
CPU when GPU init fails. `cpu` sets `QMD_FORCE_CPU=1`. The `status` output reports the device.

### Route order (adapter contract and `llm-wiki` query)

1. Identifier, code, queue or record number: exact text search over the wiki Markdown.
2. Natural-language question with no known keyword: `vector`, then confirm the found
   identifier or case with exact search.
3. Hybrid `query`: only on explicit request; slow on CPU (minutes), usable on GPU (seconds to
   about a minute in the OHR-03 measurements).

### `llm-wiki` changes

- `query` step 1–2: keep the availability probe; add the route order and name `wiki-rag` as
  the supported scaffolder for adapter `qmd-local-v1`.
- `references/tooling-tips.md`: replace the `pip install qmd` recipe with a pointer to
  `wiki-rag` (QMD is the npm package `@tobilu/qmd`).

## Failure modes

- Missing `node_modules` or models: `status` reports the reason; nothing is installed.
- GPU init failure under `auto`: QMD falls back to CPU; latency rises, results do not change.
- Wiki edited after `prepare`: `semantic-index-stale`; queries refuse rather than serve old chunks.
- Name or wiki path invalid (absolute, `..`, bad characters): scaffold refuses before writing.

## Security and data

Local-only corpus and state; the state directory and `node_modules` are git-ignored. Model
download is the only network access and happens only in `models`/`prepare`. Retrieved text is
data, not instructions; the scaffolded contract says so.

## Implementation slices

1. `wiki-rag` skill: `SKILL.md`, `scripts/scaffold.mjs`, `templates/` (adapter, contract,
   test), and `tests/` for scaffold and adapter contract. Generalized from the measured adapter.
2. `llm-wiki` query route order and the `tooling-tips.md` fix, with a test that the recipe no
   longer says `pip install qmd`.
3. Wayfinder status: OHR-03 decided, OHR-04 delivered, OHR-05 still blocked.

## Verification strategy

- Unit (CI, no `node_modules`, no models): scaffold writes the expected tree, refuses overwrite
  and bad names/paths, appends `.gitignore` once; adapter contract probe, fallback reasons,
  canonical-result checks and route mapping; `auto` leaves `QMD_FORCE_CPU` unset and `cpu`
  sets it.
- System, manual on the author's Windows machine: scaffold into a disposable project with a
  small wiki, `npm ci`, `prepare` reusing existing local models, then `search`, `vector` and
  `query`, recording times and device.
- Apple Metal: not runnable on the author's machine; stays an explicit not-run check until a
  macOS run records `device: auto` resolving to Metal.
- The OHR-03 threshold (8/10 top-3, <10 s CPU) is checked on the disposable project's fixed
  question set; one run, not a benchmark.
