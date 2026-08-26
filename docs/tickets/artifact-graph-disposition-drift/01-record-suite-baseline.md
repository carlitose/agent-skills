---
ticket_schema: 1
ticket_id: "AG-01"
execution_mode: AFK
blocked_by: []
---

# Record the test suite baseline

## Artifact Graph
- Artifact ID: `artifact:ag-01-record-suite-baseline`
- Role: `ticket`
- Parent: [artifact-graph-disposition-drift-diagnostic.md](../../specs/artifact-graph-disposition-drift-diagnostic.md)

## Parent Spec
[artifact-graph-disposition-drift-diagnostic.md](../../specs/artifact-graph-disposition-drift-diagnostic.md)

## What to Build
A recorded, named list of which tests are red on `main`, so that "regression" becomes a
measurable claim instead of an opinion.

Right now it is not measurable. A full run on `main` reported:

```
Ran 410 tests in 1033.577s
FAILED (failures=3, errors=1, skipped=1)
```

One failure is identified — `test_model_invocation_policy.py::test_every_skill_is_classified`,
with `- ['llm-wiki']`, owned by `AG-02`. The other two failures and the one error are
**unidentified**, because the run was invoked without `-v` and the captured output was
truncated to its tail.

This matters beyond tidiness. `WT-06` in this repository recorded a base of *"391 tests, 19
red (9F+10E)"* and set out to reach green; the suite is now 410 tests with 4 red. Without a
named baseline, any later change can be reported as "no regressions" while silently adding one,
which is exactly how PR #78's two new reds stayed invisible until someone counted.

The output is a short document, not code: the run command, the platform, the counts, and one
line per red test with its name and a one-line reason. It is the reference `AG-03` and every
later ticket compares against.

## Acceptance Criteria
- [ ] The suite is run on `main` with `-v` so every failure and error is named.
- [ ] Every red test is listed by its full dotted name.
- [ ] Each red test is classified as pre-existing or attributable, with the reason stated. A
      test whose cause cannot be determined is recorded as undetermined rather than guessed.
- [ ] The record names the platform and interpreter observed, because the repository already
      has platform-conditional reds — `WT-04` and `WT-06` exist for that reason.
- [ ] The record states the wall-clock time, so a later reader knows why the full suite is not
      run casually. The observed figure is ~17 minutes.
- [ ] The record is stored under `docs/` and linked from the parent spec, replacing that spec's
      "The suite baseline is unknown" unresolved question.
- [ ] Nothing in the repository is fixed by this ticket. It observes and records only.

## Frontier
Ready, no blockers, and first. `AG-03` blocks on it, because a change to `artifact_audit`
cannot be reported as regression-free against an unknown baseline.

## Step-by-Step Implementation Plan
1. Run `python -m unittest discover -s tests -t tests -v` from `ticket-autopilot/`, capturing
   the full output rather than its tail. Checkpoint: four red tests named.
2. For each red test, read it and its target to determine the cause. Checkpoint: one line per
   test, no guesses.
3. Write the record and link it from the spec. Checkpoint: the spec's unresolved question is
   deleted rather than left stale.

## Testing Plan
The deliverable is an observation, so there is nothing to unit-test. Verification is that a
second reader can re-run the recorded command and reproduce the recorded counts.

Unavailable boundary: only Windows and CPython 3.12.10 are available in this session. Any red
that is platform-conditional must say so and stays unobserved on POSIX. `pytest` is not
installed and is not required; these are stdlib `unittest` tests.

## Out of Scope
- Fixing any red test. `AG-02` owns the one identified failure; anything else found becomes a
  new ticket rather than being repaired here.
- Changing test invocation, CI, or test infrastructure.
- Running the suite on another platform.
