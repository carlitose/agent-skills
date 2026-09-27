---
ticket_schema: 1
ticket_id: "TJV-03"
execution_mode: AFK
blocked_by: []
---

# TJV-03 — Give the QA and verify judges what their questions ask about

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-judge-verdicts-03`
- Role: `ticket`
- Parent: [ticket-driver-judge-verdicts.md](../../specs/ticket-driver-judge-verdicts.md)

## Parent Spec
[ticket-driver-judge-verdicts.md](../../specs/ticket-driver-judge-verdicts.md)

## What to Build
- Pass the fresh judge its state as a hashed file instead of on the command line.
- Add the test sources the invocation ran to the QA state.
- Give the verify state the driver-observed receipt as one object.

## Acceptance Criteria
- [x] The judge prompt names `.ticket-driver/judge-state.json` and its sha256, and carries no
  state. The escalation records the same sha256. The file is gone after the judge.
  (`test_judge_reads_its_state_from_a_hashed_file_not_from_argv`, red on the TJV-01 baseline.)
- [x] The QA state lists the tracked test files, changed ones first, within the budget, with
  truncation flags. `docs/specs/` does not count as tests.
  (`test_qa_and_verify_states_carry_what_their_questions_ask_about`,
  `test_changed_tests_come_first_docs_are_not_tests_and_the_budget_truncates`; both red on the
  baseline.)
- [x] The verify state holds `driver_observed_test_receipt` with argv, exit code and output tail,
  and no longer splits the excerpt from the exit code. (Same test.)
- [x] Live probe: the corrected states decide 5 of 5 recorded cases that had gated on these
  questions: C evidence `integration` twice, TypeScript evidence `unit` twice and Python verify
  `yes` once. The probe cost about 0.08 USD. The probe's states and prose stay outside the
  repository.
- [x] 61 of 61 ticket-driver tests pass. The local quick profile, `npm run lint` and
  `artifact-audit` pass.

## Frontier
Done on 2026-09-27. TJV-02 measures the TJV-03 driver.

## Step-by-Step Implementation Plan
1. Write the RED tests for the state file, the QA sources and the verify receipt.
2. Write the state file in `Cascade.judge` and remove it in a `finally`. Add `observed_test_sources`
   to `driver.py` and use `state.observed` for the review and verify states.
3. Run the live probe on the recorded states, then the suites. Open and merge the PR.

## Testing Plan
Use the fake leaves and the fake Jev for the suites. The live probe is limited to the fresh judge
and runs outside the repository.

## Out of Scope
- Questions, thresholds and the TJV-01 verdict and retry semantics.
- Benchmark runs, which belong to TJV-02.
