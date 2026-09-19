---
type: source
title: "PSP-03 — Bound and document large-transcript ingest"
identity_key: ticket:llm-wiki-pi-session-provider/PSP-03
identity_strength: stable
source_path: docs/tickets/llm-wiki-pi-session-provider/done/03-large-transcript-bound.md
source_digest: sha256:c8b5705408e4c0317aa458e9a5791802a4eb04ae404db6506d9fac6df23d0fa4
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-15
created_provenance: git-commit
disposition_changed: 2026-09-16
disposition_changed_provenance: git-rename
run_id: c6b2211177154684
---

# PSP-03 — Bound and document large-transcript ingest

Compiled from `docs/tickets/llm-wiki-pi-session-provider/done/03-large-transcript-bound.md`. Identity is `ticket:llm-wiki-pi-session-provider/PSP-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-15** via `git-commit`
- Disposition changed: **2026-09-16** via `git-rename`

## Graph

- Parent source: [[sources/spec-llm-wiki-pi-session-provider]]
- Blocked by: [[sources/ticket-llm-wiki-pi-session-provider-psp-02]] — `ticket:llm-wiki-pi-session-provider/PSP-02`

## Run

Completed under autopilot run `c6b2211177154684`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-pi-session-provider-psp-03.md","payload_bytes":4277,"payload_sha256":"c8b5705408e4c0317aa458e9a5791802a4eb04ae404db6506d9fac6df23d0fa4"}],"payload_bytes":4277,"payload_sha256":"c8b5705408e4c0317aa458e9a5791802a4eb04ae404db6506d9fac6df23d0fa4","schema":1,"source_digest":"sha256:c8b5705408e4c0317aa458e9a5791802a4eb04ae404db6506d9fac6df23d0fa4","source_identity":"ticket:llm-wiki-pi-session-provider/PSP-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":4277,"payload_sha256":"c8b5705408e4c0317aa458e9a5791802a4eb04ae404db6506d9fac6df23d0fa4","schema":1,"source_digest":"sha256:c8b5705408e4c0317aa458e9a5791802a4eb04ae404db6506d9fac6df23d0fa4","source_identity":"ticket:llm-wiki-pi-session-provider/PSP-03"} -->
```markdown
---
ticket_schema: 1
ticket_id: "PSP-03"
execution_mode: AFK
blocked_by:
  - "PSP-02"
---

# PSP-03 — Bound and document large-transcript ingest

## Artifact Graph
- Artifact ID: `ticket:llm-wiki-pi-session-provider:PSP-03`
- Role: `ticket`
- Parent: [LLM Wiki Pi session provider](../../specs/llm-wiki-pi-session-provider.md)

## Parent Spec
[LLM Wiki Pi session provider](../../specs/llm-wiki-pi-session-provider.md), especially "Size", "Failure modes", "Alternatives considered", and "Acceptance outcomes".

## What to Build

Pi transcripts are one to two orders of magnitude larger than the supported providers'. Measured on one real project: a 574 MB transcript is 2,687 lines — about 214 KB per record, longest single line 4.9 MB, 12.9 s to stream end to end. The largest file observed in any Pi store was 1.86 GB. Claude's largest in the same wiki was 26 MB.

`extract()` already streams, so memory is bounded by the longest line rather than by the file, and the measured case needs no new mechanism. This ticket makes that a proven property instead of an assumption, and defines what happens past it.

Behavior: a transcript that can be streamed is ingested whole. A transcript that cannot — because a single record exceeds the line bound — fails naming the size it refused, per session, without aborting the other sessions and without truncating silently. Skipping the largest session quietly is rejected by the spec: it deletes the most history and leaves no mark.

Then say so where a reader will find it: the pointer text currently justifies itself with "~52 MB across this project's sessions", which is wrong the moment Pi is compiled, and the skill's provider documentation must state which providers are compiled, that `session_providers` now decides, and how to opt in.

## Acceptance Criteria
- [ ] A synthetic transcript with one record above the line bound fails naming the refused size; the other transcripts in the same run are still ingested and reported.
- [ ] The per-record bound and its rationale are stated in code and in the skill documentation, not only in a test.
- [ ] Peak memory during a large-transcript ingest is bounded by the longest record, demonstrated by a test that would fail if the file were read whole.
- [ ] One live run against a real multi-hundred-megabyte Pi transcript records wall time and peak memory as observed values; no figure is simulated or extrapolated.
- [ ] The pointer text no longer asserts a project-specific total that Pi invalidates.
- [ ] The skill documents the three supported providers, the meaning of `session_providers`, and how a wiki opts into Pi.
- [ ] No size-based silent skip exists anywhere in the path.

## Frontier

Dependency-blocked by PSP-02: the live measurement and the refusal path need a working Pi adapter to run against.

Spec Q4 (acceptable wall time for a full re-ingest) is answered by this ticket's live measurement rather than assumed beforehand: the number is recorded, and only then judged.

## Step-by-Step Implementation Plan
1. Add a generated oversized-record fixture and a RED test asserting a named refusal rather than a truncation or a crash.
2. Implement the per-record bound and the per-session failure path, keeping the rest of the run alive.
3. Add the memory-bound test that fails if the transcript is loaded whole.
4. Run the live measurement against a real large Pi transcript; record wall time and peak memory with their limits.
5. Correct the pointer text and update the skill's provider documentation.
6. Run the focused suite and a full re-ingest with `lint_wiki.py`, and simplify only after GREEN.

## Testing Plan

Automated unit and integration tests for the refusal path, the survivor behavior of other sessions, and the memory bound. One manual live run against a real Pi transcript of at least several hundred megabytes, reported with its measured wall time, peak memory, and the machine it ran on; it is evidence about that machine, not a general performance claim. Documentation changes are verified by reading, not asserted by a test.

## Out of Scope
- Any size cap that silently drops a session.
- Copying transcripts into `raw/`.
- Performance tuning of the regex scan; this ticket bounds and reports, it does not optimize.
- Pi-side changes.

```
