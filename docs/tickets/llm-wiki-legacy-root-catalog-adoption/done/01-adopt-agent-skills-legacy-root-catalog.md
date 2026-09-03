---
ticket_schema: 1
ticket_id: "WCA-01"
execution_mode: AFK
blocked_by: []
---

# Adopt the Agent Skills legacy root catalog

## Artifact Graph

- Artifact ID: `ticket:llm-wiki-legacy-root-catalog-adoption/WCA-01`
- Role: `ticket`
- Parent: [llm-wiki-legacy-root-catalog-adoption.md](../../specs/llm-wiki-legacy-root-catalog-adoption.md)

## Parent Spec

[llm-wiki-legacy-root-catalog-adoption.md](../../specs/llm-wiki-legacy-root-catalog-adoption.md)

## What to Build

Implement the spec's explicit, digest-bound legacy root-catalog adoption boundary. It must insert the three canonical WS-08 ownership blocks without automatic heading inference, prove lossless marker removal and replay, and leave ordinary compilation fail-closed for arbitrary unmarked catalogs.

Apply that boundary to the exact tracked `knowledge/wiki/index.md`, assigning only its current generated project, session, and timeline regions. Then validate the normal compiler against disposable copies so the post-integration hook can update the tracked Agent Skills wiki through its separate candidate flow.

## Acceptance Criteria

- [ ] Adoption requires the exact legacy SHA-256 plus a complete ordered, non-overlapping map for `project-sources`, `session-sources`, and `timeline`.
- [ ] Removing only the six inserted marker lines reproduces the original `knowledge/wiki/index.md` bytes exactly; all resulting markers parse once and replay is byte-idempotent.
- [ ] Wrong digest, missing owner, overlap, wrong order, malformed UTF-8, special path, duplicated/nested/conflicting marker, or unknown owner fails before catalog mutation.
- [ ] Ordinary ingest and sync continue to reject arbitrary unmarked catalogs rather than infer ownership from headings.
- [ ] The exact migrated repository wiki completes ingest, timeline rebuild, generated-scope validation, and all lint passes in staging.
- [ ] A tracked fixture returns a truthful wiki-sync candidate and unchanged replay without mutating its protected tree.
- [ ] Full LLM Wiki, Ticket Autopilot wiki-sync, context/token, compile, diff, and Artifact Graph checks remain green.

## Frontier

Ready. The downstream Omicron Code wayfinder remains deferred until this implementation and its separate wiki update are terminal.

## Step-by-Step Implementation Plan

1. Freeze the exact legacy index digest and explicit ownership map as regression evidence.
2. Add the narrow adoption API/CLI beside `root_catalog.py`, with pre-write and post-write identity checks.
3. Add unit and staged-sync tests for success, replay, tamper, ambiguity, and ordinary fail-closed behavior.
4. Apply the migration to the tracked Agent Skills catalog without hand-editing generated entries.
5. Run complete wiki and runner regression boundaries and document the explicit recovery path.

## Testing Plan

Unit tests cover map, digest, parser, round-trip, replay, newline, and failure invariants. Integration tests use disposable tracked and untracked wiki fixtures through `sync_project`. Repository checks validate the migrated exact catalog, full LLM Wiki suite, relevant Ticket Autopilot tests, context/token checks, compileall, diff check, and Artifact Graph delta. The real generated wiki update remains the later runner-owned post-integration boundary.

## Out of Scope

- Automatic adoption of arbitrary legacy indexes.
- Omicron Code implementation, Pi package composition, or local Pi settings.
- Direct publication or merge of a wiki candidate.
- Applying unrelated audit corrections or changing generated wiki entries by hand.
