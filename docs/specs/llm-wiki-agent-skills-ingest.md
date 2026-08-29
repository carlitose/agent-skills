# Agent Skills Tracked Project Wiki Ingest

## Artifact Graph

- Artifact ID: `artifact:llm-wiki-agent-skills-ingest`
- Role: `spec`
- Parent: [LLM Wiki as a Project History Knowledge Base](llm-wiki-project-history-wayfinder.md)

### Children

- [AWI-01 Keep session digests in the wiki catalog](../tickets/llm-wiki-agent-skills-ingest/01-keep-session-digests-in-the-wiki-catalog.md)
- [AWI-02 Build the tracked Agent Skills project wiki](../tickets/llm-wiki-agent-skills-ingest/02-build-the-tracked-agent-skills-project-wiki.md)

## Type

Feature spec

## Status

Accepted and ready for ticket execution.

## Decision source

The user confirmed the instance policy on 2026-08-29:

- create the project wiki inside this repository at `knowledge/` and track it in Git;
- ingest the repository's documentation, specs, tickets, research, and prototypes;
- represent matching agent sessions only as pointers plus bounded attributed digests, never as
  copied transcripts;
- exclude secret material and private-file contents;
- keep Markdown canonical and introduce no RAG, vector database, retrieval service, or graph
  expansion in this slice.

This resolves the only open instance-placement decision in the parent Wayfinder. It does not
select any retrieval tier from the separate Obsidian/hybrid-retrieval investigation.

## Current behavior

The repository has the complete application-independent `llm-wiki` compiler but no compatible
wiki root. Post-integration `wiki-sync-v1` therefore reports `skipped/absent`.

A disposable proof against current `main` established the actual initial corpus:

- `ingest_docs.py` classified 147 project artefacts with eight weak identities;
- `session_ingest.py` discovered 208 Codex sessions, five unresolved Codex records, and no
  Claude session for this checkout, representing 607,844,264 transcript bytes without copying
  those transcripts;
- scaffold, project artefacts, session pointers/digests, and timeline produced 669 files;
- the timeline produced 226 events, 97 lifecycle records, two period pages, and ten unknown
  dates with explicit reasons;
- lint failed with 208 `index-drift` errors because every generated session digest was absent
  from `wiki/index.md`, plus 215 warnings.

The error is deterministic and blocks a durable ingest. `session_ingest.py` writes digest pages
but does not update the catalog, while `ingest_docs.py::_write_index` rebuilds the catalog from
project artefacts alone and would erase any session-only entries after a later docs change.

## Goals

1. Make session digest catalog ownership explicit and idempotent across both session and project
   document re-ingest.
2. Scaffold a tracked `knowledge/` instance bound to the canonical Agent Skills checkout.
3. Compile every configured project artefact into identity-stable source pages.
4. Add only pointer metadata and bounded attributed digest pages for matching sessions.
5. Build the ticket lifecycle timeline with provenance-bearing dates and explicit unknowns.
6. Deliver a wiki with zero lint errors and a recorded, classified warning baseline.
7. Leave the wiki usable through ordinary Markdown, wikilinks, and an optional Obsidian editor
   with every retrieval component absent.

## Non-goals

- Copying transcript JSONL, provider databases, environment dumps, credentials, or arbitrary
  files outside the configured project-doc globs.
- Ingesting the three local Obsidian/RAG notes from `Downloads/`; their source-copy policy and
  content synthesis remain a separate initiative.
- Adding embeddings, BM25 services, pgvector, qmd, PostgreSQL, HTTP, MCP, query caches, inferred
  graph edges, or an Obsidian plugin.
- Fixing the separately reproduced `sync_project.py` lifecycle bug under another provenance
  trail.
- Claiming that warnings are errors or silently suppressing session pages that have no inbound
  lifecycle link.

## Target behavior

### Tracked wiki root

`knowledge/` uses the one accepted layout:

```text
knowledge/
├── llm-wiki-project.json
├── purpose.md
├── schema.md
├── audit/README.md
├── audit/resolved/
├── raw/{sources,refs,assets}/
└── wiki/
    ├── index.md
    ├── log.md
    ├── concepts/ entities/ sources/ queries/ comparisons/ synthesis/
    └── timeline/tickets/
```

Every committed wiki path is a regular, non-executable UTF-8 Markdown or binding JSON file.
There are no symlinks, copied transcript files, databases, indexes, caches, or application-owned
private state.

### Project binding and source scope

`llm-wiki-project.json` binds the wiki to the canonical checkout used for ongoing local sync,
uses `git_mode: auto`, keeps `auto_sync: enabled`, and configures only:

- `docs/specs/*.md`;
- `docs/tickets/**/*.md`;
- `docs/research/*.md`;
- `docs/prototypes/**/*.md`.

A repository artefact page carries identity, source path, source digest, disposition, graph
links, and date provenance. It summarizes metadata and lifecycle; it does not copy the source
body into a second canonical location.

### Session privacy boundary

Each discovered session may create exactly:

- one `raw/refs/<provider>-<session-id>.md` pointer containing provider, local external path,
  size, record count, timestamps, and staleness signals;
- one `wiki/sources/session-<provider>-<session-id>.md` digest bounded by the existing
  session-ingest contract and explicitly attributed to the session rather than asserted as
  project truth.

Transcript JSONL is never copied. Candidate QA scans generated content for private-key blocks,
common credential/token prefixes, populated Authorization/Bearer material, and connection
credentials. Any match blocks delivery pending redaction; passing this bounded scan is not a
claim of arbitrary-secret detection.

### Shared catalog ownership

`wiki/index.md` lists every wiki page exactly once through reachable catalogs.

- Session ingest adds or refreshes one deterministic `Session sources` catalog section whenever
  session pages change.
- Project-doc ingest preserves and rebuilds that section from the session pages already present.
- Repeating either operation cannot duplicate a session entry.
- A later project-doc amendment cannot remove session entries.
- Timeline catalogs remain nested under `wiki/timeline/index.md` and keep their existing rules.

### Health and repeatability

The initial candidate runs scaffold, docs ingest, session ingest, timeline build, and all fifteen
lint passes. Delivery requires zero lint errors. Warnings remain visible and are grouped by pass
with causes; no numeric warning baseline is frozen before the catalog fix is exercised on the
final corpus.

A second docs ingest on unchanged project artefacts reports zero changed pages. A repeated
session ingest writes only a session whose source transcript actually grew during the run and
never creates a second identity. Rebuilding the timeline preserves one lifecycle page per ticket.

## Semantic invariants

- Markdown and the tracked wiki tree remain the only canonical knowledge state.
- The wiki compiler never edits project source artefacts or Ticket Envelopes.
- Ticket pages remain keyed by family and ticket ID across `done/`, `canceled/`, and `hold/`
  moves; stable Artifact IDs remain stable across source moves.
- Every stated date carries a provenance rung; unresolved dates render as `unknown` with a
  reason.
- Session claims remain attributed to the session and cannot become project facts merely by
  ingestion.
- A catalog entry is navigation, not evidence and not an inbound citation for orphan analysis.
- The wiki's existence does not authorize its later tracked sync candidate to merge.
- Obsidian compatibility remains optional and no application-private state becomes input.

## Failure modes

| Failure | Required behavior |
|---|---|
| Session digest missing from catalog | Lint error; AWI-01 must repair catalog ownership before instance delivery |
| Later docs ingest drops session entries | Regression failure; no wiki candidate may be delivered |
| Binding missing, malformed, or points to a missing checkout | Fail closed before ingest |
| Ticket parser unavailable or rejects a ticket | Fail the docs ingest; do not classify the ticket as a weaker artefact |
| Transcript grows during execution | Rewrite only its pointer/digest and report it; do not duplicate identity |
| Transcript disappears or cannot be resolved | Preserve/report the pointer state through existing lint; never invent content |
| Credential-pattern scan matches generated content | Stop delivery and redact or exclude the causal source |
| Lint has any error | Stop delivery with the failing passes and paths |
| Wiki candidate includes forbidden file kind/path | Reject the candidate before commit |
| Post-integration tracked wiki sync finds a diff | Freeze a fresh WikiSyncRef and require separate wiki authorization |

## Implementation slices

### AWI-01 — catalog-safe session ingest

Repair the shared catalog contract with focused unit and integration tests. Session ingestion
must update its section, project-doc index rebuild must preserve it, and replay must not duplicate
entries. A temporary full pipeline must reach zero `index-drift` errors for session pages.

### AWI-02 — tracked Agent Skills instance

Scaffold `knowledge/`, replace purpose placeholders with the accepted project scope, bind it,
run docs/session/timeline ingest, classify warnings, scan the generated boundary for credential
patterns and forbidden file kinds, run full lint, and record current corpus counts. No optional
retrieval component is installed or configured.

## Verification strategy

### Unit

- Seed session pages into a scaffold and assert deterministic index section insertion,
  replacement, removal of duplicates, and ordering.
- Rebuild the docs index after session ingest and assert every session entry remains exactly
  once.
- Seed a private-key/token/Authorization fixture into the candidate scanner and prove it fails.

### Integration

- Run scaffold → docs ingest → session ingest → timeline → docs re-ingest → lint in a temporary
  wiki with fixture sessions; require zero errors and exact session identities.
- Build the real `knowledge/` candidate and run all fifteen lint passes.
- Parse every ticket through canonical `ticket-parse`, compare project artefact count to wiki
  identities, and require one lifecycle page per ticket.
- Compare the candidate path inventory against the allowed regular UTF-8 Markdown/JSON scope.

### System/local

- Record current docs, session, byte, page, timeline, provenance, unknown-date, lint, and warning
  counts without treating them as immutable requirements.
- Open representative source, session, and lifecycle pages from `wiki/index.md` and follow one
  level of wikilinks with no external application.

### Live/provider

No provider behavior is needed to prove wiki content. Ticket delivery and any later tracked
wiki-sync candidate use Ticket Autopilot's normal exact-head provider gates and separate merge
authority.
