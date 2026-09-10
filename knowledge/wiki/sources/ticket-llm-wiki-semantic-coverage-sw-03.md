---
type: source
title: "Compile structured semantic content"
identity_key: ticket:llm-wiki-semantic-coverage/SW-03
identity_strength: stable
source_path: docs/tickets/llm-wiki-semantic-coverage/done/03-compile-structured-semantic-content.md
source_digest: sha256:5ce18dc6d3514c62f431f51879485101e8f05623d976d5d20d4037976bc75a88
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-05
created_provenance: git-commit
disposition_changed: 2026-09-10
disposition_changed_provenance: git-rename
run_id: sw-semantic-coverage
---

# Compile structured semantic content

Compiled from `docs/tickets/llm-wiki-semantic-coverage/done/03-compile-structured-semantic-content.md`. Identity is `ticket:llm-wiki-semantic-coverage/SW-03`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-05** via `git-commit`
- Disposition changed: **2026-09-10** via `git-rename`

## Graph

- Parent source: [[sources/artifact-llm-wiki-semantic-coverage-wayfinder]]
- Blocked by: [[sources/ticket-llm-wiki-semantic-coverage-sw-02]] — `ticket:llm-wiki-semantic-coverage/SW-02`

## Run

Completed under autopilot run `sw-semantic-coverage`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-semantic-coverage-sw-03.md","payload_bytes":3909,"payload_sha256":"5ce18dc6d3514c62f431f51879485101e8f05623d976d5d20d4037976bc75a88"}],"payload_bytes":3909,"payload_sha256":"5ce18dc6d3514c62f431f51879485101e8f05623d976d5d20d4037976bc75a88","schema":1,"source_digest":"sha256:5ce18dc6d3514c62f431f51879485101e8f05623d976d5d20d4037976bc75a88","source_identity":"ticket:llm-wiki-semantic-coverage/SW-03","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3909,"payload_sha256":"5ce18dc6d3514c62f431f51879485101e8f05623d976d5d20d4037976bc75a88","schema":1,"source_digest":"sha256:5ce18dc6d3514c62f431f51879485101e8f05623d976d5d20d4037976bc75a88","source_identity":"ticket:llm-wiki-semantic-coverage/SW-03"} -->
```markdown
---
ticket_schema: 1
ticket_id: "SW-03"
execution_mode: AFK
blocked_by:
  - "SW-02"
---

# Compile structured semantic content

## Artifact Graph
- Artifact ID: `artifact:sw-03-compile-structured-semantic-content`
- Role: `ticket`
- Parent: [LLM Wiki semantic coverage recovery](../../specs/llm-wiki-semantic-coverage-wayfinder.md)

## Parent Spec
[LLM Wiki semantic coverage recovery](../../specs/llm-wiki-semantic-coverage-wayfinder.md)

## What to Build
Implement the semantic projection contract confirmed by `SW-02` in the project-history ingest path. Extend the source model and renderer so generated source pages carry the required, source-grounded semantic content for every configured artefact kind rather than only title, digest, provenance, graph, dates, and run metadata.

The implementation must preserve the existing identity-keyed, set-based transition model. Semantic-only source changes must update visible page content; unchanged replay must still write zero bytes; ticket disposition moves must still update one stable page; and canonical Ticket Envelope metadata must still come only from `ticket-parse`.

Update the public skill and schema documentation so compiled source pages, provenance, authored-versus-preserved content, splitting, and freshness behavior match the confirmed decision.

## Acceptance Criteria
- [ ] `Artefact` or a deeper internal projection type carries all semantic inputs required by the `SW-02` contract without introducing a second ticket-envelope parser.
- [ ] Rendered ticket pages expose build intent, acceptance criteria, testing plan, frontier, and exclusions according to the confirmed policy.
- [ ] Specs, research, prototypes, and guides receive their confirmed per-kind projection, including explicit behavior for missing or irregular headings.
- [ ] A semantic-only edit changes visible compiled content and the page digest/markers required by lint.
- [ ] Re-ingesting an unchanged corpus writes zero bytes, and a disposition move updates exactly one identity-stable page.
- [ ] Existing graph links, date provenance, run links, weak-identity warnings, and tombstones remain correct.
- [ ] Generated content stays within the confirmed size/splitting bounds and identifies preserved versus agent-authored material exactly as decided.
- [ ] `SKILL.md`, schema guidance, and tests document one consistent production contract.

## Frontier
Dependency-blocked on the confirmed HITL decision `SW-02`. Once that decision is integrated, this ticket is AFK.

## Step-by-Step Implementation Plan
1. Translate the decision into one internal semantic projection boundary with per-kind rules and explicit failure outcomes.
2. Extend classification and rendering while retaining canonical metadata and identity ownership. Checkpoint: representative source pages contain both old provenance data and new semantic content.
3. Integrate projection freshness with existing new/changed/moved/missing/unchanged transitions. Checkpoint: semantic edits, moves, tombstones, and no-op replay behave causally.
4. Update docs and corpus fixtures. Checkpoint: documented page shape equals emitted page shape.
5. Run focused and full `llm-wiki` regressions and record any unavailable external boundary.

## Testing Plan
Add unit tests for each artefact kind, missing/irregular sections, semantic-only edits, deterministic replay, disposition moves, tombstones, weak identities, canonical blocker parsing, graph links, and size/splitting bounds. Run the full `llm-wiki` test suite and a scratch ingest over the repository corpus.

Manual inspection should answer the diagnostic's representative ticket questions from generated pages alone. Do not mutate a production wiki or claim GUI/vector-search behavior.

## Out of Scope
- The independent semantic-coverage lint implementation in `SW-04`.
- Historical gate causes or source-publication repair.
- Changing Ticket Envelope v1.

```
