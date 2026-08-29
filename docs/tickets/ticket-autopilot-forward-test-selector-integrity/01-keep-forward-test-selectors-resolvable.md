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
