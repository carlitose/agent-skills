---
type: source
title: "Enforce semantic coverage in wiki lint"
identity_key: ticket:llm-wiki-semantic-coverage/SW-04
identity_strength: stable
source_path: docs/tickets/llm-wiki-semantic-coverage/done/04-enforce-semantic-coverage-lint.md
source_digest: sha256:7f5a77fe32a929e89063dc6695ea7e3312fe11ccc081cca2ff9e7101d3e5ce26
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-09-05
created_provenance: git-commit
disposition_changed: 2026-09-10
disposition_changed_provenance: git-rename
run_id: sw-semantic-coverage
---

# Enforce semantic coverage in wiki lint

Compiled from `docs/tickets/llm-wiki-semantic-coverage/done/04-enforce-semantic-coverage-lint.md`. Identity is `ticket:llm-wiki-semantic-coverage/SW-04`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-05** via `git-commit`
- Disposition changed: **2026-09-10** via `git-rename`

## Graph

- Parent source: [[sources/artifact-llm-wiki-semantic-coverage-wayfinder]]
- Blocked by: [[sources/ticket-llm-wiki-semantic-coverage-sw-02]] — `ticket:llm-wiki-semantic-coverage/SW-02`
- Blocked by: [[sources/ticket-llm-wiki-semantic-coverage-sw-03]] — `ticket:llm-wiki-semantic-coverage/SW-03`

## Run

Completed under autopilot run `sw-semantic-coverage`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-llm-wiki-semantic-coverage-sw-04.md","payload_bytes":3356,"payload_sha256":"7f5a77fe32a929e89063dc6695ea7e3312fe11ccc081cca2ff9e7101d3e5ce26"}],"payload_bytes":3356,"payload_sha256":"7f5a77fe32a929e89063dc6695ea7e3312fe11ccc081cca2ff9e7101d3e5ce26","schema":1,"source_digest":"sha256:7f5a77fe32a929e89063dc6695ea7e3312fe11ccc081cca2ff9e7101d3e5ce26","source_identity":"ticket:llm-wiki-semantic-coverage/SW-04","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3356,"payload_sha256":"7f5a77fe32a929e89063dc6695ea7e3312fe11ccc081cca2ff9e7101d3e5ce26","schema":1,"source_digest":"sha256:7f5a77fe32a929e89063dc6695ea7e3312fe11ccc081cca2ff9e7101d3e5ce26","source_identity":"ticket:llm-wiki-semantic-coverage/SW-04"} -->
```markdown
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

```
