---
type: source
title: "Discover and synchronize the tracked wiki from the exact source checkout"
identity_key: ticket:llm-wiki-exact-source-checkout-sync/WXS-01
identity_strength: stable
source_path: docs/tickets/llm-wiki-exact-source-checkout-sync/done/01-sync-tracked-wiki-from-exact-source.md
source_digest: sha256:48a1d67b807da8bc6fd3d01a0ccde31e4e8e7d3cafff160f5d0f69a60cbe95d6
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-01
created_provenance: git-commit
disposition_changed: 2026-09-01
disposition_changed_provenance: git-rename
run_id: agent-skills-wiki-exact-source-sync-v2-20260901
---

# Discover and synchronize the tracked wiki from the exact source checkout

Compiled from `docs/tickets/llm-wiki-exact-source-checkout-sync/done/01-sync-tracked-wiki-from-exact-source.md`. Identity is `ticket:llm-wiki-exact-source-checkout-sync/WXS-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-01** via `git-commit`
- Disposition changed: **2026-09-01** via `git-rename`

## Graph

- Parent source: [[sources/spec-llm-wiki-exact-source-checkout-sync]]

## Run

Completed under autopilot run `agent-skills-wiki-exact-source-sync-v2-20260901`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-exact-source-checkout-sync-wxs-01.md","payload_bytes":4283,"payload_sha256":"48a1d67b807da8bc6fd3d01a0ccde31e4e8e7d3cafff160f5d0f69a60cbe95d6"}],"payload_bytes":4283,"payload_sha256":"48a1d67b807da8bc6fd3d01a0ccde31e4e8e7d3cafff160f5d0f69a60cbe95d6","schema":1,"source_digest":"sha256:48a1d67b807da8bc6fd3d01a0ccde31e4e8e7d3cafff160f5d0f69a60cbe95d6","source_identity":"ticket:llm-wiki-exact-source-checkout-sync/WXS-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4283,"payload_sha256":"48a1d67b807da8bc6fd3d01a0ccde31e4e8e7d3cafff160f5d0f69a60cbe95d6","schema":1,"source_digest":"sha256:48a1d67b807da8bc6fd3d01a0ccde31e4e8e7d3cafff160f5d0f69a60cbe95d6","source_identity":"ticket:llm-wiki-exact-source-checkout-sync/WXS-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "WXS-01"
execution_mode: AFK
blocked_by: []
---

# Discover and synchronize the tracked wiki from the exact source checkout

## Artifact Graph
- Artifact ID: `ticket:llm-wiki-exact-source-checkout-sync:WXS-01`
- Role: `ticket`
- Parent: [LLM Wiki exact-source checkout sync](../../specs/llm-wiki-exact-source-checkout-sync.md)

## Parent Spec
[LLM Wiki exact-source checkout sync](../../specs/llm-wiki-exact-source-checkout-sync.md)

## What to Build
Repair `wiki-sync-v1` so post-integration synchronization discovers the existing tracked Agent Skills `knowledge/` wiki from the exact detached source checkout while validating its binding against the canonical persistent project root.

Separate the transient physical wiki path from its stable canonical logical identity, classify generated-path tracking in the same-Git-common source checkout, freeze tracked output as a separate candidate, and keep both protected checkouts unchanged. After integration, synchronize the production repository wiki and retain the zero-error lint receipt and separate wiki publication gate.

## Acceptance Criteria
- [ ] With an alternate exact `source_root` and no explicit wiki roots, discovery checks only that source root and direct children.
- [ ] The binding must resolve exactly to the canonical project root; source-worktree or other-path bindings remain `broken-binding`.
- [ ] Logical wiki identity is canonical-root plus a safe relative path and is stable across temporary source checkout paths.
- [ ] Canonical and source roots must be worktrees of one Git common directory; aliases, symlinks, escapes, submodules, and another repository fail closed.
- [ ] Generated tracking is classified in the source checkout; partial tracking remains an error and explicit external roots retain direct-write semantics.
- [ ] Source head/corpus and wiki compare-and-swap state are rechecked before publication.
- [ ] Internal tracked output creates the normal frozen candidate without dirtying either checkout or changing the binding.
- [ ] Ticket-batch invocation from a mismatched worktree still reports literal `broken-binding`.
- [ ] The production Agent Skills sync produces a tracked candidate or unchanged result with zero wiki lint errors.
- [ ] Any generated wiki PR stops at separate exact-head authorization; no application authority transfers.

## Frontier
Ready AFK. Wiki publication may stop later at its manual exact-head gate.

## Step-by-Step Implementation Plan
1. Introduce a physical-discovery/logical-identity representation for wiki candidates.
2. Use alternate exact source checkout bounded discovery only when explicit roots are absent.
3. Validate canonical binding and shared Git common directory without path-equivalence shortcuts.
4. Classify tracking through the source checkout and freeze tracked output in canonical Git-common state.
5. Bind deterministic identity, source head/state, and replay to the normalized result.
6. Add positive, negative, concurrency, and regression tests across LLM Wiki and Ticket Autopilot.
7. After integration and local Pi sync, run the production post-integration wiki effect and record its candidate/lint/PR state.

## Testing Plan
- Unit tests for identity normalization, compatibility, classification, and deterministic replay.
- Temporary-Git integration fixture with stale canonical checkout and exact linked checkout containing a tracked wiki.
- Negatives for binding mismatch, other Git repository, symlink/escape, submodule, partial tracking, stale source, and concurrent drift.
- Existing absent, external, internal-untracked, ticket-batch, candidate delivery, and authorization tests.
- Full LLM Wiki, Ticket Autopilot wiki-sync, forward matrix, Artifact Graph, ticket contract/inventory, extension, and context-budget suites.
- Production lint receipt must report zero errors; warnings remain visible and do not become fabricated success.

## Out of Scope
- Rebinding the wiki or weakening checkout-specific binding.
- Scaffolding a new wiki or changing purpose/schema/raw/audit files.
- OHR retrieval selection, external-note ingest, Obsidian, embeddings, or vector services.
- Automatically authorizing or merging the generated wiki PR.
- Unrelated run, status, Pi, or Betsharemarket work.

```
