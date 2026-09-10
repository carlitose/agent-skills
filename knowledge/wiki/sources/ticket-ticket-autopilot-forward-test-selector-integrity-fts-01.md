---
type: source
title: "Keep forward-test selectors resolvable"
identity_key: ticket:ticket-autopilot-forward-test-selector-integrity/FTS-01
identity_strength: stable
source_path: docs/tickets/ticket-autopilot-forward-test-selector-integrity/done/01-keep-forward-test-selectors-resolvable.md
source_digest: sha256:a6064e81e00c913105171dc92a210351b8dda36bda802f208e3695e71ee1c553
source_status: present
artefact_kind: ticket
disposition: completed
created: 2026-08-29
created_provenance: git-commit
disposition_changed: 2026-08-29
disposition_changed_provenance: git-rename
run_id: fts-selector-integrity-20260829
---

# Keep forward-test selectors resolvable

Compiled from `docs/tickets/ticket-autopilot-forward-test-selector-integrity/done/01-keep-forward-test-selectors-resolvable.md`. Identity is `ticket:ticket-autopilot-forward-test-selector-integrity/FTS-01`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-29** via `git-commit`
- Disposition changed: **2026-08-29** via `git-rename`

## Graph

- Parent source: [[sources/artifact-ticket-autopilot-forward-test-selector-integrity-diagnostic]]

## Run

Completed under autopilot run `fts-selector-integrity-20260829`, taken from the `completion.json` beside the source. That sidecar carries no date, so nothing here is dated from it.

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"acceptance":{"headings":[4],"status":"present"},"exclusions":{"headings":[8],"status":"present"},"frontier":{"headings":[5],"status":"present"},"intent":{"headings":[3],"status":"present"},"testing":{"headings":[7],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/ticket-ticket-autopilot-forward-test-selector-integrity-fts-01.md","payload_bytes":2502,"payload_sha256":"a6064e81e00c913105171dc92a210351b8dda36bda802f208e3695e71ee1c553"}],"payload_bytes":2502,"payload_sha256":"a6064e81e00c913105171dc92a210351b8dda36bda802f208e3695e71ee1c553","schema":1,"source_digest":"sha256:a6064e81e00c913105171dc92a210351b8dda36bda802f208e3695e71ee1c553","source_identity":"ticket:ticket-autopilot-forward-test-selector-integrity/FTS-01","source_kind":"ticket"} -->

| Topic | Source sections |
|---|---|
| intent | 3: What to Build |
| acceptance | 4: Acceptance Criteria |
| testing | 7: Testing Plan |
| frontier | 5: Frontier |
| exclusions | 8: Out of Scope |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2502,"payload_sha256":"a6064e81e00c913105171dc92a210351b8dda36bda802f208e3695e71ee1c553","schema":1,"source_digest":"sha256:a6064e81e00c913105171dc92a210351b8dda36bda802f208e3695e71ee1c553","source_identity":"ticket:ticket-autopilot-forward-test-selector-integrity/FTS-01"} -->
```markdown
---
ticket_schema: 1
ticket_id: "FTS-01"
execution_mode: AFK
blocked_by: []
---

# Keep forward-test selectors resolvable

## Artifact Graph

- Artifact ID: `artifact:fts-01-keep-forward-test-selectors-resolvable`
- Role: `ticket`
- Parent: [Forward-test Selector Integrity Diagnostic](../../specs/ticket-autopilot-forward-test-selector-integrity-diagnostic.md)

## Parent Spec

[Forward-test Selector Integrity Diagnostic](../../specs/ticket-autopilot-forward-test-selector-integrity-diagnostic.md)

## What to Build

Repair the stale semantic reconciliation selector in the forward-test matrix and add a fast
regression that proves every matrix reference resolves to an existing Python test definition.
Keep zero-test commands fail-closed and avoid adding a duplicate integration-test alias.

## Acceptance Criteria

- [ ] The `autonomous-merge-grant` scenario selects
      `test_semantic_stack_reconciliation_refreshes_advancing_target_and_rebinds_bundle`.
- [ ] A focused unit test walks every `TestRef`, requires its selected test file to exist, and
      requires its method to be a defined `test_*` function in that file.
- [ ] A planted missing method makes the selector-integrity check fail without executing the
      expensive forward matrix.
- [ ] The repaired semantic selector executes at least one test and passes.
- [ ] The complete `test_forward_test.py` suite and ticket-autopilot unit suite pass.
- [ ] The affected forward-test scenario passes with no `NO TESTS RAN` command result.

## Frontier

Ready. The stale selector is reproduced on current `main`; the intended renamed test already
passes and needs no implementation change.

## Step-by-Step Implementation Plan

1. Add the selector-integrity regression against the current matrix and observe it fail on the
   stale method.
2. Update the single stale `TestRef` to the current semantic reconciliation test name.
3. Add a planted missing-method assertion that proves the guard's negative path.
4. Run the focused current selector, forward-test unit suite, repaired scenario, and complete
   runner suite.

## Testing Plan

Use Python AST inspection for the fast matrix integrity regression. Execute the current
semantic test and the affected scenario as causal checks, then run all ticket-autopilot tests.

## Out of Scope

- Duplicating or aliasing the renamed semantic integration test.
- Changing scenario prompts, evidence classes, or retained-artifact shape.
- Treating an empty unittest selection as passing evidence.

```
