# Ask Skills Execution Tool Discipline

## Artifact Graph

- Artifact ID: `spec:ask-skills-execution-tool-discipline`
- Role: `spec`
- Standalone: true

### Children

- [ATD-01 — Enforce routed tool-use defaults](../tickets/ask-skills-execution-tool-discipline/01-enforce-routed-tool-use-defaults.md)

## Type

Feature spec.

## Status

Approved by the user's explicit request. Ready for ticket decomposition and isolated delivery.

## Problem

`ask-skills` reliably selects the smallest skill flow, but it does not remind the routed
agent which cross-cutting tools should carry non-trivial work. Agents can therefore skip a
project wiki during research, perform multi-step code processing as repeated individual tool
calls, or let the visible plan become stale.

The `llm-wiki` query operation currently scans compiled Markdown. Its contract explicitly
uses a compiled wiki instead of mandatory retrieve-raw-on-every-query RAG. Repository research
shows an optional `qmd` recipe and completed hybrid-retrieval research/benchmark artifacts, but
OHR-03 has not selected a production retrieval tier. No RAG or hybrid adapter is currently a
supported query path. Mere documentation, an installed binary, an MCP server, or index files
must not be mistaken for an active capability.

## Goal

Make `ask-skills` state three concise execution defaults after routing:

1. use a compatible project-bound LLM Wiki as the first research index, prefer a supported and
   bound RAG/hybrid query path when one is genuinely available, and verify material claims
   against primary sources;
2. use the `code` tool supplied by `pi-code-tool` for suitable multi-step code workflows,
   mechanical transformations, aggregation, and programmatic checks;
3. create and maintain `update_plan` (Pi Plan) for non-trivial multi-step work.

Also sharpen `llm-wiki`'s `query` operation so it probes the supported retrieval capability,
records which mode it used, and falls back explicitly to compiled Markdown when no valid
RAG/hybrid path exists.

## Non-Goals

- Implementing, selecting, installing, or downloading a RAG, vector, embedding, database,
  qmd, HTTP, or MCP retrieval adapter.
- Making the wiki a substitute for source artifacts or primary external documentation.
- Requiring a wiki for questions outside a compatible bound corpus, or scaffolding/mutating a
  wiki during an otherwise read-only request.
- Forcing `code` for one small authored edit, prose-only work, or a task for which direct
  `read`/`edit`/`write` is clearer.
- Treating `pi-code-tool` auto-approval as repository, provider, publication, merge, wiki,
  synchronization, migration, cleanup, release, or reload authority.
- Creating a second plan representation or using Pi Plan for trivial one-step requests.
- Replacing or weakening current merge-all, ticket lifecycle, delivery-lane, and exact-authority
  routing rules.

## Current Behavior

- `ask-skills/SKILL.md` owns routing and names skill compositions, but has no cross-cutting
  execution-tool section.
- `llm-wiki/SKILL.md` query steps read `wiki/index.md`, relevant pages, and one wikilink level.
- `llm-wiki/references/tooling-tips.md` documents qmd as genuinely optional.
- `docs/specs/llm-wiki-obsidian-hybrid-retrieval-wayfinder.md` says no retrieval adapter is
  selected and keeps RAG-derived state optional and non-canonical.
- The Pi tool is named `update_plan`; “Pi Plan” is explanatory language, not an invented alias.
- The `pi-code-tool` integration exposes the tool as `code`; its availability and approval
  configuration do not widen any workflow authority.

## Target Contract

### Ask Skills execution defaults

Add one concise section after the routing map and before the response contract. It remains a
routing-level reminder and must not duplicate specialist workflows.

For a non-trivial routed request:

- **Plan:** if `update_plan` is available, initialize it after route selection, keep exactly one
  step `in_progress`, update the complete snapshot at meaningful phase/status changes, and
  finish or clear it at handoff. If unavailable, state that once and continue without
  inventing tool evidence.
- **Research:** when the repository or topic has a compatible bound LLM Wiki, query it first as
  an index. Before that query, apply the RAG availability contract below. Follow wiki
  provenance to repository artifacts or primary external sources before making material
  factual claims. If no compatible wiki exists, continue with ordinary primary-source
  research; do not scaffold one by inference.
- **Code:** when `code` is available, prefer it for loops, filtering, aggregation, repeated
  inspection, mechanical/derived transformations, and programmatic validation. Keep a small
  judgment-driven authored edit in direct `edit`/`write` when that is clearer. A tool's local
  auto-approval changes no repository or provider authority.

A trivial request may omit Pi Plan and code mode. The agent should not call a tool merely to
satisfy a checkbox when it adds no useful work.

### RAG availability contract

A RAG/hybrid wiki query path is “available” only when **both** are true:

1. the active `llm-wiki` contract and the selected bound wiki configuration explicitly name a
   supported retrieval mode/adapter for that wiki; and
2. its required tool or command is already present and usable inside the request's declared
   privacy, network, dependency, and authority boundary.

The following are insufficient on their own: an optional recipe, a package or executable on
`PATH`, an MCP server definition, an index/cache directory, research or benchmark prose, or a
future roadmap ticket.

When available, use the supported RAG/hybrid path to choose context, then ground and cite the
answer in canonical wiki pages and their provenance. Retrieval chunks, scores, vectors,
embeddings, graph projections, and caches remain derived evidence rather than wiki truth.

When unavailable, use the existing compiled-Markdown query: read the index, selected pages,
and one explicit wikilink level. State `compiled-markdown` and a concise fallback reason; do
not auto-install, download, start, configure, or authenticate a retrieval component.

The current repository baseline must exercise the fallback because it has no selected
supported RAG/hybrid adapter.

### Query mode visibility

Every `llm-wiki` query response states one mode:

- `rag/hybrid:<adapter-id>` plus the exact supported binding used; or
- `compiled-markdown` plus `no-supported-rag-binding` or another concrete failure reason.

A durable query page includes the same mode in its body unless the active wiki schema defines
a dedicated field. The mode statement is evidence of routing, not proof that retrieved
content is correct.

## Semantic Invariants

- The wiki is an index and compiled knowledge source, not primary evidence.
- Canonical Markdown, provenance, audit history, and lint remain authoritative when derived
  retrieval state is absent or deleted.
- RAG preference never authorizes installation, network access, provider calls, credential
  use, source ingestion, durable query mutation, or index creation.
- `code` preference never bypasses tool approval, delivery stages, CandidateRef binding, or
  exact-head provider guards.
- Pi Plan reflects the current workflow state; it never becomes a second scheduler or ticket
  ledger.
- `ask-skills` continues to own routing only. `llm-wiki`, `pi-code-tool`, specialist skills,
  and Ticket Autopilot retain their existing ownership.
- Current repository-wide merge intent and lifecycle routing text remains byte-for-byte or
  semantically preserved and remains covered by existing tests.

## Failure Modes

| Failure | Required behavior |
|---|---|
| No compatible wiki root | Continue primary-source research and state that no wiki query was used. |
| Wiki exists but no supported RAG binding | Use `compiled-markdown`; state `no-supported-rag-binding`. |
| Adapter named but tool/command absent | Fall back without installation and report the unavailable dependency. |
| Adapter would cross undeclared privacy/network/credential boundary | Do not use it; fall back and report the boundary. |
| RAG results lack canonical page/provenance support | Do not promote them to a factual claim; read canonical sources or report insufficient evidence. |
| `code` unavailable or unsuitable | Use direct canonical tools and state no false code-mode claim. |
| `update_plan` unavailable | Continue with one concise textual status; do not fabricate a plan-tool result. |
| Existing Ask Skills authority text drifts | Fail tests and reject delivery. |

## Implementation Slices

One tracer-bullet ticket is sufficient:

- update `ask-skills/SKILL.md` with the three execution defaults;
- update `llm-wiki/SKILL.md` query steps with supported RAG/hybrid detection, visible mode, and
  safe fallback;
- add focused contract tests while preserving all existing routing assertions;
- adjust only the explicit Ask Skills line budget if concise wording cannot remain within the
  current 70-line cap;
- update controlled context-cost documentation only if repository tests identify it as a
  required public surface.

## Verification Strategy

Automated checks must prove:

- Ask Skills names `llm-wiki`, `code`, and `update_plan` and defines non-trivial/trivial
  boundaries;
- wiki lookup precedes broad research only for a compatible bound corpus and primary-source
  verification remains mandatory;
- RAG/hybrid use requires both an explicit supported binding and an already usable adapter;
- optional qmd prose, installed artifacts, MCP declarations, caches, and roadmap documents do
  not count as availability;
- the no-adapter baseline selects `compiled-markdown` with a visible reason and performs no
  install/download/start/auth action;
- code mode is preferred for compositional/programmatic work but not forced for a single
  authored edit;
- Pi Plan is initialized and refreshed for non-trivial work without becoming workflow
  authority;
- merge-all, lifecycle, single-ticket, and delivery-lane routing contracts remain intact;
- skill line/context budgets, Markdown, Artifact Graph, and exact CandidateRef checks pass.

No test may claim a live RAG adapter was exercised unless a separate exact fixture supplies a
supported binding and adapter. The current ticket needs static contract coverage, not a
network or provider call.

## Acceptance Criteria

- [ ] `ask-skills/SKILL.md` explicitly states the LLM Wiki/RAG, Pi Code Tool, and Pi Plan
      defaults with availability and trivial-task limits.
- [ ] `llm-wiki/SKILL.md` query steps detect only a supported bound RAG/hybrid path, prefer it
      when valid, and visibly fall back to compiled Markdown otherwise.
- [ ] The current no-adapter baseline is described as fallback, not as active RAG.
- [ ] Wiki-derived claims still require canonical page provenance and primary-source checks.
- [ ] `code` and `update_plan` preferences do not widen repository/provider authority or
      duplicate specialist ownership.
- [ ] Focused tests prevent regression and all existing Ask Skills routing tests remain green.
- [ ] No RAG dependency, index, cache, service, provider call, install, or wiki mutation is
      introduced by this change.
