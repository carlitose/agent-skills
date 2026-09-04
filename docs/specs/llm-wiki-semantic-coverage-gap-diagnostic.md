# LLM Wiki Semantic Coverage Gap

## Artifact Graph
- Artifact ID: `artifact:llm-wiki-semantic-coverage-gap-diagnostic`
- Role: `spec`
- Parent: [LLM Wiki semantic coverage recovery](llm-wiki-semantic-coverage-wayfinder.md)

## Type
Diagnostic

## Status
Confirmed from code; corpus measurements and external ledger findings are user-reported.

## Summary

The project-history ingest creates one identity-stable wiki source page per repository artefact,
but it does not compile the artefact's semantic content. The resulting wiki can answer provenance,
identity, graph, disposition, and timeline questions; it cannot directly answer what a spec decided
or what a ticket requires.

This is a contract gap rather than accidental data destruction. The source documents remain the
authority. The existing implementation deliberately treated semantic summarization and content
quality as out of scope.

## Evidence

### Compiler behavior

`llm-wiki/scripts/ingest_docs.py` reads each source document while classifying it, but `Artefact`
retains only identity and lifecycle metadata: path, digest, kind, disposition, title, Artifact Graph
relations, blockers, run ID, and dates. `render_page()` therefore emits front matter, a provenance
paragraph, dates, graph links, and run metadata; it has no source body or structured source sections
to render.

This matches the original delivery contract:

- `docs/tickets/llm-wiki-project-history/done/05-ingest-repository-docs.md` explicitly excludes
  "summarising artefact content beyond what a source page needs" and defines the work as provenance
  and structure rather than a rewrite;
- `docs/tickets/llm-wiki-project-history/done/11-drift-and-coverage-lint.md` explicitly excludes
  semantic or content-quality checks on wiki prose.

The supplied controlled test changed a spec's body completely and observed only a digest change in
the compiled page. That result follows directly from the current data model and renderer.

### Corpus impact

The supplied diagnosis reports 201 metadata-only pages:

| Artefact category | Pages without semantic content |
|---|---:|
| Tickets | 109 |
| Specs | 47 |
| Guides, research, and prototypes | 45 |
| **Total** | **201** |

The corresponding sources reportedly contain about 978 KB and 121,726 words. All 109 ticket pages
omit executable sections such as `What to Build`, `Acceptance Criteria`, `Testing Plan`, `Frontier`,
and `Out of Scope`. The observed wiki also contains no concept, query, synthesis, comparison, or
entity pages. These measurements describe the diagnosed wiki instance and have not been reproduced
in this checkout.

### Lint blind spot

The structural lint validates layout, links, catalogs, logs, and audits. The drift lint validates
source existence, digest freshness, identity uniqueness, provenance, timeline coverage, session
pointers, and ingest coverage. None establishes that a page carries any semantic projection of its
source. A metadata-only page with the correct digest is therefore healthy under every current pass.

### Source durability risk

The supplied diagnosis also found eight Markdown documents that are local, ignored, and untracked in
the source project. Four concern NightDAX Delayed Shadow work. They are absent from `origin/main` and
from the wiki because the configured discovery surface does not materialize them. This is not the
same failure as metadata-only compilation: those documents have no durable repository copy and need
a separate source-ownership repair in their owning repository.

### Gate explanation loss

`ticket-autopilot/scripts/autopilot/kernel.py` accepts `record_stage(..., result="gated")` without a
reason and opens a stage gate with the generated text `<stage> reported a gate`.
`ticket-autopilot/scripts/autopilot/cli.py` likewise requires only `stage`, `result`, and
`expected_tree_oid` for a stage event. `Kernel.report()` exposes only IDs through `open_gates`, so
`status` does not carry the corresponding gate record or reason.

The supplied ledger scan reports four historical stage gates with generic reasons and two still open,
including NightDAX ticket 25. A precise historical reason cannot be reconstructed from generic text
alone. Any repair must bind a replacement reason to actual evidence rather than inventing one.

## Root Cause

The original project-history slice optimized for stable identity, idempotent re-ingest, provenance,
and lifecycle reconstruction. Semantic compilation was expressly deferred. The compiler's model,
renderer, tests, and lint consequently agree on a metadata-only contract. The gate issue has the same
shape at a different boundary: the transition records that a gate exists, but its input contract does
not require the reason that makes the gate actionable.

## Required Target Behavior

1. Every compiled repository artefact has an explicit, source-grounded semantic projection suitable
   for direct wiki queries while retaining identity, digest, provenance, graph, and lifecycle data.
2. Semantic coverage is machine-checkable. A current digest and a page file are insufficient when the
   required semantic projection is absent, empty, stale, or malformed.
3. A stage gate cannot be created without a specific non-empty cause, and status exposes structured
   open-gate records including their causes.
4. Historical generic reasons remain marked as unavailable until evidence-backed repair; no migration
   fabricates causes.
5. Ignored and untracked source documents are secured in their owning repository independently of wiki
   compilation.

## Semantic Invariants

- Repository documents remain primary evidence; the wiki is a compiled projection with source links.
- Existing identity keys, move handling, normalized source digests, tombstones, graph links, date
  provenance, and no-op re-ingest behavior remain intact.
- A source change that affects projected meaning updates the semantic body, not only front matter.
- Coverage rules are defined per artefact kind and do not pass merely because arbitrary prose exists.
- Ticket Envelope fields continue to come from the canonical parser; semantic extraction must not
  introduce a second parser for ticket metadata.
- Gate reasons are required at the transition boundary and are visible at the read boundary.
- Existing durable ledgers are never silently reinterpreted or assigned invented historical evidence.

## Unresolved Decisions

- The semantic projection contract: deterministic section preservation, authored summaries and concept
  pages, or a layered combination.
- Required sections and minimum coverage for specs, tickets, research, prototypes, and guides.
- Whether semantic compilation remains deterministic and stdlib-only or introduces an agent-authored
  compile phase with explicit freshness and audit semantics.
- How old open gates receive an evidence-backed reason, and how irrecoverable historical generic gates
  are represented.

## Acceptance Outcomes

- Changing a representative source's semantic section changes visible wiki content in that page, not
  only `source_digest`.
- A representative ticket page exposes `What to Build`, `Acceptance Criteria`, `Testing Plan`,
  `Frontier`, and `Out of Scope` according to the confirmed projection contract.
- A seeded metadata-only page fails a named semantic-coverage lint pass; a correctly compiled page
  passes it.
- Re-ingesting an unchanged corpus writes zero bytes, and disposition moves still update one stable
  page rather than creating duplicates.
- Recording a new `gated` stage result without a specific cause fails closed.
- `status` returns each open gate's ID, owner, kind, state, and reason in structured form.
- Legacy generic reasons are visible as legacy/unknown or explicitly refreshed from durable evidence;
  they are never guessed.
- The eight reported untracked documents are either durably published or explicitly dispositioned in
  their owning repository before their local copies can be treated as recoverable.

## Fix Direction

First prototype and confirm the semantic projection and coverage contract. Then implement semantic
compilation and its lint as separate, causally linked slices. The gate transition/status correction
can proceed independently, while evidence-backed repair of old gate records and external untracked
sources remains a separate follow-up.
