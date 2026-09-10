---
type: source
title: "Preserve hand-written root catalog sections during sync"
identity_key: ticket:llm-wiki-docs-only-autosync/WS-08
identity_strength: stable
source_path: docs/tickets/llm-wiki-docs-only-autosync/done/08-preserve-hand-written-root-catalog-sections.md
source_digest: sha256:20d0a6034a2ae8275c665104e73e87442e5425a79f4d47d4d800bd8cc170df3b
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-01
created_provenance: git-commit
disposition_changed: 2026-09-02
disposition_changed_provenance: git-rename
run_id: llm-wiki-root-catalog-preservation-20260902
---

# Preserve hand-written root catalog sections during sync

Compiled from `docs/tickets/llm-wiki-docs-only-autosync/done/08-preserve-hand-written-root-catalog-sections.md`. Identity is `ticket:llm-wiki-docs-only-autosync/WS-08`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-01** via `git-commit`
- Disposition changed: **2026-09-02** via `git-rename`

## Graph

- Parent source: [[sources/artifact-llm-wiki-docs-only-autosync-wayfinder]]

## Run

Completed under autopilot run `llm-wiki-root-catalog-preservation-20260902`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-docs-only-autosync-ws-08.md","payload_bytes":5307,"payload_sha256":"20d0a6034a2ae8275c665104e73e87442e5425a79f4d47d4d800bd8cc170df3b"}],"payload_bytes":5307,"payload_sha256":"20d0a6034a2ae8275c665104e73e87442e5425a79f4d47d4d800bd8cc170df3b","schema":1,"source_digest":"sha256:20d0a6034a2ae8275c665104e73e87442e5425a79f4d47d4d800bd8cc170df3b","source_identity":"ticket:llm-wiki-docs-only-autosync/WS-08","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":5307,"payload_sha256":"20d0a6034a2ae8275c665104e73e87442e5425a79f4d47d4d800bd8cc170df3b","schema":1,"source_digest":"sha256:20d0a6034a2ae8275c665104e73e87442e5425a79f4d47d4d800bd8cc170df3b","source_identity":"ticket:llm-wiki-docs-only-autosync/WS-08"} -->
```markdown
---
ticket_schema: 1
ticket_id: "WS-08"
execution_mode: AFK
blocked_by: []
---

# Preserve hand-written root catalog sections during sync

## Artifact Graph
- Artifact ID: `artifact:ws-08-preserve-hand-written-root-catalog-sections`
- Role: `ticket`
- Parent: [llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## Parent Spec
[llm-wiki-docs-only-autosync-wayfinder.md](../../specs/llm-wiki-docs-only-autosync-wayfinder.md)

## What to Build
Fix the root-catalog ownership bug recorded in the parent wayfinder. `ingest_docs.py::_write_index()` currently reconstructs all of `wiki/index.md` from project artefacts, retained tombstones, timeline state, and session entries. Because `sync_project.py` invokes that writer in the staging copy, any docs transition can remove hand-written concept, entity, query, open-work, or other non-owned catalog sections while still producing a lint-clean candidate.

Implement an ownership-preserving catalog update. Generated project/session/timeline navigation must remain complete and deterministic, while every existing non-owned block remains byte-identical and in the same order. The implementation must reject ambiguous ownership rather than guessing or overwriting. Apply the same contract to direct ingest and the composed `sync-project` boundary.

The user-provided audit reference `audit/20260901-160000-index-sobrescrito.md` was unavailable in the planning checkout. Do not invent or resolve its contents; the executable regression derives from the reproduced full-file writer and fixture-owned manual blocks.

## Acceptance Criteria
- [ ] A fixture root index contains generated sections plus hand-written concept, entity, and open-work sections before, between, and after generated content; a project-doc change followed by direct ingest preserves every manual block byte-for-byte and in order.
- [ ] The same fixture through `sync-project` updates generated source/tombstone/session/timeline entries, preserves manual blocks exactly, returns a truthful changed-path/CandidateRef result, and passes every `lint_wiki.py` pass with zero errors.
- [ ] A second unchanged ingest and sync are idempotent: no index rewrite, no duplicate generated/manual entry, and no candidate diff.
- [ ] Missing, duplicated, malformed, nested, or conflicting generated ownership boundaries fail closed before protected-wiki application; the result identifies the causal index failure.
- [ ] Existing scaffold, session-catalog, timeline-catalog, retained-tombstone, exact-source, tracked/untracked/external, concurrency, and compare-and-swap behavior remains green.
- [ ] The implementation never treats arbitrary headings as generated ownership, never deletes unknown manual content, and never requires a human to rebuild the index after a normal sync.
- [ ] No external wiki, tracked `knowledge/` instance, audit correction, provider object, local Pi package, retrieval architecture, or DRV artifact is mutated by tests.

## Frontier
Ready. This is the only open WS frontier; WS-01 through WS-07 remain completed.

## Step-by-Step Implementation Plan
1. Freeze mixed-ownership index fixtures and a destructive regression that demonstrates the current full-file overwrite through direct ingest and `sync-project`.
2. Introduce the smallest deterministic generated-block ownership representation and parser, preserving all non-owned bytes and ordering; reject ambiguous or malformed state.
3. Refactor `_write_index()` to render generated project/tombstone/timeline content through that bounded owner and continue composing the existing deterministic session section without taking whole-file ownership.
4. Align scaffold/templates and existing compatible indexes with the chosen representation without silently claiming arbitrary legacy sections.
5. Add direct-ingest, session/timeline composition, full sync, tracked-candidate, lint, idempotency, tamper, and no-protected-tree-mutation tests.
6. Document the mixed-ownership contract and the recovery path for a pre-fix index without applying any real audit note or publishing a generated wiki candidate.

## Testing Plan
- Unit: generated-block parser/rendering, byte preservation, deterministic ordering, duplicate/missing/malformed boundary rejection, newline fidelity, and session-section composition.
- Integration: scaffold → seed manual blocks → docs/session/timeline ingest → docs change → ingest again → lint; assert exact manual-byte hashes and current generated entries.
- System/local: run `sync-project` only against disposable internal-untracked, internal-tracked, and external fixtures; validate changed paths, candidate digest, compare-and-swap, retry, and unchanged replay.
- Regression: run the full LLM Wiki suite and the Ticket Autopilot wiki-sync forward matrix. Record unavailable live/provider boundaries rather than simulating authority.

## Out of Scope
- Reconstructing or publishing the real Agent Skills wiki index.
- Applying, moving, or resolving `audit/20260901-160000-index-sobrescrito.md`.
- General wiki compile/restructure behavior outside root-catalog ownership.
- Retrieval, embeddings, Obsidian application behavior, or test-selection policy.
- Changing wiki publication, merge, exact-source, local-Pi, or audit-correction authority.

```
