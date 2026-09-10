---
ticket_schema: 1
ticket_id: "SW-04"
execution_mode: AFK
blocked_by:
  - "SW-02"
  - "SW-03"
---

# Enforce semantic coverage in wiki lint

## Artifact Graph
- Artifact ID: `artifact:sw-04-enforce-semantic-coverage-lint`
- Role: `ticket`
- Parent: [LLM Wiki semantic coverage recovery](../../specs/llm-wiki-semantic-coverage-wayfinder.md)

## Parent Spec
[LLM Wiki semantic coverage recovery](../../specs/llm-wiki-semantic-coverage-wayfinder.md)

## What to Build
Add an independent semantic-coverage lint pass that validates generated source pages against the per-kind contract confirmed by `SW-02` and emitted by `SW-03`. A page with a current `source_digest`, valid identity, and complete metadata must fail when its required semantic projection is absent, empty, malformed, mismatched to its artefact kind, or stale under the confirmed markers.

The pass must remain source-grounded and deterministic. It checks the declared projection contract rather than grading prose quality or trusting arbitrary non-empty text. Integrate its name, severity, repair guidance, seeded-defect tests, and pass count into the public lint documentation.

## Acceptance Criteria
- [ ] A named semantic-coverage pass runs for every present project-history source page and reports not-applicable truthfully when no project binding exists.
- [ ] A metadata-only page with a current source digest fails.
- [ ] Empty, malformed, wrong-kind, incomplete required-section, and stale-projection fixtures each fail with actionable output.
- [ ] Correctly compiled ticket, spec, research, prototype, and guide fixtures pass.
- [ ] Arbitrary prose cannot satisfy the pass without the exact decision-defined structure and source binding.
- [ ] Tombstones and explicitly unsupported legacy pages follow the exact `SW-02` policy rather than silently passing.
- [ ] Every seeded defect proves the pass can turn red; a clean full wiki remains reachable.
- [ ] `SKILL.md`, tests, and lint output agree on the pass name, severity, total pass count, and repair guidance.

## Frontier
Dependency-blocked on `SW-02` for policy and `SW-03` for the production page shape. AFK after both integrate.

## Step-by-Step Implementation Plan
1. Convert the confirmed projection markers and per-kind rules into one lint-owned validator without duplicating ingest parsing logic.
2. Add seeded defects for each missing/malformed/stale class and clean fixtures for every artefact kind.
3. Integrate the pass into the structural/drift driver at the decided severity. Checkpoint: metadata-only pages now make the full lint non-green as intended.
4. Update public documentation and the test that keeps documented operations aligned with code.
5. Run focused, full wiki, non-Git, ignored-docs, and scratch-corpus checks.

## Testing Plan
Unit tests cover each failure class, tombstones, legacy policy, absent binding, non-Git hosts, ignored docs, and clean fixtures. Integration tests run ingest followed by lint, then remove or corrupt only semantic projection data while preserving metadata and digest to prove causal detection.

No subjective prose scoring, LLM judge, GUI, vector index, or production wiki mutation is required.

## Out of Scope
- Generating or repairing semantic content automatically from lint.
- Changing source identity, digest, graph, or timeline contracts.
- Gate-reason behavior.
