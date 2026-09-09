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
