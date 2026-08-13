---
ticket_schema: 1
ticket_id: "WT-03"
execution_mode: AFK
blocked_by:
  - "WT-02"
---

# Implement the decided decoding `errors` policy

## Artifact Graph
- Artifact ID: `artifact:wt-03-implement-decoding-errors-policy`
- Role: `ticket`
- Parent: [windows-text-fidelity-wayfinder.md](../../specs/windows-text-fidelity-wayfinder.md)

## Parent Spec
[windows-text-fidelity-wayfinder.md](../../specs/windows-text-fidelity-wayfinder.md)

## What to Build
Apply the policy confirmed in `WT-02` to all five `subprocess.run` call sites in
`git_ops.py`, and reconcile `test_utf8_io.py` with it so the invariant is asserted rather
than merely held.

Current state on CandidateRef `acd881c`: `errors="replace"` at every site, and
`test_command_runner_decodes_stdout_and_stderr_as_utf8` fails with `'strict' != 'replace'`.
On base `d306799` the same test is green. This ticket ends with that test green again,
asserting whatever `WT-02` decided.

## Acceptance Criteria
- [ ] Every `subprocess.run` call site in `git_ops.py` matches the decided policy.
- [ ] `test_utf8_io.py` asserts the decided policy and passes.
- [ ] A non-ASCII payload still survives the runner character-identical, preserving
      `WD-02`'s third acceptance criterion.
- [ ] If the decision separates diagnostic from data paths, a test covers each path
      distinctly.
- [ ] If the decision permits `replace` anywhere a value feeds an equality check, a test
      documents what happens to an undecodable byte there.

## Frontier
Dependency-blocked on `WT-02`. No implementation may begin before that decision is
confirmed; guessing the policy here is what produced the regression in the first place.

## Step-by-Step Implementation Plan
1. Read the decision spec produced by `WT-02`.
2. Apply it to `SubprocessCommandRunner.run`, `run_git`, `origin_url`, and both call sites
   in `assert_cleanup_safe`. Checkpoint: no site left at a default.
3. Update `test_utf8_io.py` to assert the decision. Checkpoint: green.
4. Add the path-distinguishing tests the decision implies.

## Testing Plan
Automated: `test_utf8_io` plus any new per-path tests. Manual: reproduce a provider failure
on a non-English Windows locale and confirm the diagnostic is readable — this is the
observation that motivated the change and it is not covered by any automated test today.

## Out of Scope
- Choosing the policy, which is `WT-02`.
- The body round trip, which is `WT-01`.
