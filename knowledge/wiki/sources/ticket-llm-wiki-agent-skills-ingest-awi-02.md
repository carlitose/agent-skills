---
type: source
title: "Build the tracked Agent Skills project wiki"
identity_key: ticket:llm-wiki-agent-skills-ingest/AWI-02
identity_strength: stable
source_path: docs/tickets/llm-wiki-agent-skills-ingest/done/02-build-the-tracked-agent-skills-project-wiki.md
source_digest: sha256:bcf621d93e163aae5997ee8e30ee85a1a9675bacfe0dfd5589be98ead1b340ae
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-30
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Build the tracked Agent Skills project wiki

Compiled from `docs/tickets/llm-wiki-agent-skills-ingest/done/02-build-the-tracked-agent-skills-project-wiki.md`. Identity is `ticket:llm-wiki-agent-skills-ingest/AWI-02`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-30** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Parent source: [[sources/artifact-llm-wiki-agent-skills-ingest]]
- Blocked by: [[sources/ticket-llm-wiki-agent-skills-ingest-awi-01]] — `ticket:llm-wiki-agent-skills-ingest/AWI-01`

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-agent-skills-ingest-awi-02.md","payload_bytes":4551,"payload_sha256":"bcf621d93e163aae5997ee8e30ee85a1a9675bacfe0dfd5589be98ead1b340ae"}],"payload_bytes":4551,"payload_sha256":"bcf621d93e163aae5997ee8e30ee85a1a9675bacfe0dfd5589be98ead1b340ae","schema":1,"source_digest":"sha256:bcf621d93e163aae5997ee8e30ee85a1a9675bacfe0dfd5589be98ead1b340ae","source_identity":"ticket:llm-wiki-agent-skills-ingest/AWI-02","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4551,"payload_sha256":"bcf621d93e163aae5997ee8e30ee85a1a9675bacfe0dfd5589be98ead1b340ae","schema":1,"source_digest":"sha256:bcf621d93e163aae5997ee8e30ee85a1a9675bacfe0dfd5589be98ead1b340ae","source_identity":"ticket:llm-wiki-agent-skills-ingest/AWI-02"} -->
```markdown
---
ticket_schema: 1
ticket_id: "AWI-02"
execution_mode: AFK
blocked_by:
  - "AWI-01"
---

# Build the tracked Agent Skills project wiki

## Artifact Graph

- Artifact ID: `artifact:awi-02-build-agent-skills-wiki`
- Role: `ticket`
- Parent: [Agent Skills Tracked Project Wiki Ingest](../../specs/llm-wiki-agent-skills-ingest.md)

## Parent Spec

[Agent Skills Tracked Project Wiki Ingest](../../specs/llm-wiki-agent-skills-ingest.md)

## What to Build

Create the accepted tracked wiki at `knowledge/`, bind it to the canonical Agent Skills
checkout, compile the configured project documentation, add session pointers and attributed
digests without copying transcripts, build the lifecycle timeline, classify warnings, and
deliver a zero-error lint state with no retrieval infrastructure.

Move the tracked `AWI-02` planning mirror into its completion path in the same candidate so the
compiled wiki and delivered ticket lifecycle describe the state that will exist after
integration.

## Acceptance Criteria

- [ ] `knowledge/` contains the one accepted layout, a filled project-specific `purpose.md`, the
      standard `schema.md`, `audit/`, `raw/`, `wiki/`, and an enabled project binding restricted
      to the four accepted documentation globs.
- [ ] Every candidate path under `knowledge/` is a regular non-executable UTF-8 Markdown file or
      the binding JSON; there are no symlinks, databases, binary assets, caches, transcript
      copies, application-private state, or retrieval artifacts.
- [ ] Every configured current project artefact has exactly one identity-stable source page and
      every ticket has exactly one lifecycle page with provenance-bearing dates or an explicit
      `unknown` reason.
- [ ] Every matched session creates one pointer and one bounded attributed digest; transcript
      JSONL content is not copied, duplicate identities are absent, and unresolved sessions are
      reported.
- [ ] The generated candidate passes a bounded credential-pattern scan for private-key blocks,
      common token prefixes, populated Authorization/Bearer material, and connection
      credentials; any match blocks delivery.
- [ ] All fifteen wiki lint passes complete with zero errors. Warnings are grouped by pass,
      explained, and retained rather than suppressed.
- [ ] A second unchanged docs ingest writes zero project pages; a repeated session ingest writes
      only sources that actually grew and does not duplicate catalog entries; timeline rebuild
      preserves one lifecycle page per ticket.
- [ ] Representative project source, session digest, and lifecycle pages are reachable from
      `wiki/index.md` through ordinary Markdown/wikilinks with no application or retrieval
      service.
- [ ] Current corpus counts and limitations are recorded as evidence, not frozen as future
      constants.

## Frontier

Blocked by `AWI-01`. It becomes ready only after session catalog ownership is integrated and its
full-pipeline regression is green.

## Step-by-Step Implementation Plan

1. Scaffold `knowledge/` with title `Agent Skills Project Knowledge` and the selected project
   binding.
2. Replace purpose placeholders with the confirmed scope, questions, exclusions, and thesis.
3. Run project docs ingest through the canonical Ticket Autopilot parser.
4. Run session pointer/digest ingest, then build the provenance-bearing timeline.
5. Re-run docs/session/timeline operations to measure idempotence and live-session growth.
6. Run the credential-pattern and candidate-path boundary checks before staging.
7. Run full wiki lint, classify every warning family, and repair every error.
8. Record exact current counts and validate representative navigation paths.

## Testing Plan

Run the complete `llm-wiki` suite plus the real local scaffold/ingest/session/timeline/lint
pipeline. Assert candidate file kinds, modes, UTF-8 decoding, binding, identity uniqueness,
source/timeline coverage, transcript non-copying, credential scan, exact tree identity, and
rerun behavior. Provider delivery checks remain owned by Ticket Autopilot.

## Out of Scope

- Copying the three Obsidian/RAG notes from `Downloads/`.
- Full transcripts, provider SQLite databases, environment dumps, or arbitrary private files.
- RAG, embeddings, BM25 services, qmd, pgvector, PostgreSQL, inferred graph edges, query caches,
  HTTP, MCP, or an Obsidian plugin.
- Repairing separately tracked `sync_project.py` lifecycle defects.
- Autonomous merge authority for either the application PR or a later tracked wiki-sync
  candidate.

```
