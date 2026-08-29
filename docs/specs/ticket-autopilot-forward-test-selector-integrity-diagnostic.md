# Ticket Autopilot Forward-test Selector Integrity Diagnostic

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-forward-test-selector-integrity-diagnostic`
- Role: `spec`
- Standalone: true

### Children

- [Keep forward-test selectors resolvable](../tickets/ticket-autopilot-forward-test-selector-integrity/01-keep-forward-test-selectors-resolvable.md)

## Diagnosis Report - lens: repro-first

### Root cause

The `autonomous-merge-grant` forward-test scenario still names
`test_semantic_stack_reconciliation_rebinds_the_fresh_verified_bundle`, but RT-01 renamed
that test to
`test_semantic_stack_reconciliation_refreshes_advancing_target_and_rebinds_bundle` while
expanding its target-refresh coverage. The forward-test matrix was not updated in the same
change, and its matrix-shape tests verify scenario IDs and record structure but do not prove
that every `TestRef` method still exists in its selected test module.

### Evidence

- `ticket-autopilot/scripts/forward_test.py` line 221 retains the old method name.
- `ticket-autopilot/tests/test_cli.py` defines only the new method name.
- Running the exact matrix command with `unittest discover ... -k` reports `Ran 0 tests`,
  `NO TESTS RAN`, and exits with status 5.
- Running the new selector directly succeeds; the full runner suite also reaches that test.
- `git blame` binds the stale matrix entry to the semantic-rebind change and the rename to
  RT-01 commit `3540328d513a9a5767e733d12c6e488339f1ee90`.

### Feedback loop built

The minimal reproduction is the exact `TestRef.command()` emitted for the stale selector.
A regression should inspect every matrix reference and fail before the workflow run when its
pattern is missing or its method is not defined in that Python test file.

### Fix location and approach

Update the selector in `ticket-autopilot/scripts/forward_test.py`. Add a fast structural
regression in `ticket-autopilot/tests/test_forward_test.py` that parses every referenced test
file and verifies each method name is a real `test_*` function definition. This keeps the
guard independent of executing the expensive forward matrix and catches future renames in the
ordinary unit suite.

### Alternatives ruled out

- The semantic reconciliation implementation is not failing: its current test passes.
- Treating `NO TESTS RAN` as success would hide missing evidence and weaken the workflow.
- Adding an alias test would duplicate an expensive integration case and preserve stale
  naming rather than repairing the matrix contract.
- Running the entire forward matrix inside `test_forward_test.py` would detect the issue but
  impose unnecessary runtime when an AST-level selector integrity check is sufficient.

### Confidence: high

The exact stale name, rename commit, zero-test exit, and missing matrix integrity assertion are
all directly observed.

## Current Behavior

The forward workflow reports one failed command and one failed scenario even though the
intended semantic reconciliation regression passes under its current name.

## Target Invariants

- Every forward-test `TestRef` resolves to an existing selected test file and a defined
  `test_*` function.
- A test rename that leaves the matrix stale fails the small forward-test unit suite.
- Zero executed tests never count as passing workflow evidence.
- The semantic target-refresh and fresh-bundle rebind regression remains the selected causal
  test; no duplicate alias is introduced.

## Verification Strategy

- Red/green regression that replaces one matrix reference with a missing name and observes
  the selector-integrity assertion fail.
- Run the `test_forward_test.py` suite.
- Run the repaired `autonomous-merge-grant` scenario and confirm every selected command runs.
- Run the complete ticket-autopilot unit suite.

## Non-goals

- Redesigning the forward-test scenario catalog.
- Renaming the current semantic reconciliation test again.
- Changing unittest exit semantics or accepting zero-test evidence.

