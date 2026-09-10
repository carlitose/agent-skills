---
type: source
title: "Adopt the Agent Skills legacy root catalog"
identity_key: ticket:llm-wiki-legacy-root-catalog-adoption/WCA-01
identity_strength: stable
source_path: docs/tickets/llm-wiki-legacy-root-catalog-adoption/done/01-adopt-agent-skills-legacy-root-catalog.md
source_digest: sha256:cf77d917dbbf3ef9965a8c1d5068ac387bdd40ebc64fffef18bdb47f37086778
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-03
created_provenance: git-commit
disposition_changed: 2026-09-03
disposition_changed_provenance: git-rename
run_id: llm-wiki-legacy-root-catalog-adoption-v2-20260903
---

# Adopt the Agent Skills legacy root catalog

Compiled from `docs/tickets/llm-wiki-legacy-root-catalog-adoption/done/01-adopt-agent-skills-legacy-root-catalog.md`. Identity is `ticket:llm-wiki-legacy-root-catalog-adoption/WCA-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-03** via `git-commit`
- Disposition changed: **2026-09-03** via `git-rename`

## Graph

- Parent source: [[sources/spec-llm-wiki-legacy-root-catalog-adoption]]

## Run

Completed under autopilot run `llm-wiki-legacy-root-catalog-adoption-v2-20260903`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-legacy-root-catalog-adoption-wca-01.md","payload_bytes":3545,"payload_sha256":"cf77d917dbbf3ef9965a8c1d5068ac387bdd40ebc64fffef18bdb47f37086778"}],"payload_bytes":3545,"payload_sha256":"cf77d917dbbf3ef9965a8c1d5068ac387bdd40ebc64fffef18bdb47f37086778","schema":1,"source_digest":"sha256:cf77d917dbbf3ef9965a8c1d5068ac387bdd40ebc64fffef18bdb47f37086778","source_identity":"ticket:llm-wiki-legacy-root-catalog-adoption/WCA-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3545,"payload_sha256":"cf77d917dbbf3ef9965a8c1d5068ac387bdd40ebc64fffef18bdb47f37086778","schema":1,"source_digest":"sha256:cf77d917dbbf3ef9965a8c1d5068ac387bdd40ebc64fffef18bdb47f37086778","source_identity":"ticket:llm-wiki-legacy-root-catalog-adoption/WCA-01"} -->
```markdown
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

```
