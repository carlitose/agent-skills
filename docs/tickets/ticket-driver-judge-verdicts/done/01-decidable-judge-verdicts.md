---
ticket_schema: 1
ticket_id: "TJV-01"
execution_mode: AFK
blocked_by: []
---

# TJV-01 — Give the fresh judge a decidable verdict and the driver's test receipt

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-judge-verdicts-01`
- Role: `ticket`
- Parent: [ticket-driver-judge-verdicts.md](../../specs/ticket-driver-judge-verdicts.md)

## Parent Spec
[ticket-driver-judge-verdicts.md](../../specs/ticket-driver-judge-verdicts.md)

## What to Build
Build the judge's verdict lines and parser from the question registry. Put the driver-observed
test receipt in the review state. In c2a and c3a, send a decisive review negative into the run's
single builder retry. Uncertainty keeps failing closed to the human gate.

## Acceptance Criteria
- [x] The judge prompt lists the question's criteria and `Answer:` lines. Only a single final
  `Answer:` line with an allowed value decides the question. Every other ending is `uncertain`,
  and sentences elsewhere in the prose are never matched. All five `choice` and `noul` questions
  that can escalate are covered, including `qa.evidence_class` and `retry.recoverable`
  `environment-failure`. Covered by `tests/test_verdicts.py`, which checks every escalating
  question, nine fail-closed endings and a verdict mentioned inside a sentence.
  `test_fresh_judge_decides_evidence_class_from_its_final_answer` and
  `test_quoted_clean_sentence_is_not_the_judge_verdict` failed on the baseline.
- [x] The review state includes the driver-observed test argv, exit code and a bounded output tail.
  The QA and verify states are unchanged. The Jev request and the judge prompt carry it
  (`test_review_state_carries_the_driver_observed_test_receipt`, red on the baseline).
- [x] In c2a and c3a, a decisive `findings_block=yes` or `scope_complete=no` runs builder 2 once
  with the finding, then retests, rechecks the candidate and gates again. The retry budget is
  shared with the directed-review retry. A persistent negative gates, and an uncertain answer
  gates without a retry. Covered by five tests: `test_decisive_scope_negative_reenters_the_one_builder_retry`,
  `test_persistent_scope_negative_gates_after_one_retry`,
  `test_c2a_jev_blocker_buys_one_builder_retry_then_gates`, the builder-2 assertion added to
  `test_uncertainty_uses_fresh_judge_and_then_gates_on_ambiguity`, and the unchanged
  `test_c3a_directed_blocker_retries_once_and_rechecks_tests_and_semantics` for the shared
  budget.
- [x] Each new test fails on the baseline and passes after the change. The c1b, c2 and c3 suites,
  ruff, the file-limit lint and the local quick profile all stay green. On the baseline: 11
  failures and 1 import error. After the change: 58 of 58 ticket-driver tests pass, the local
  quick profile passes 16 of 16 checks, `npm run lint` passes and `artifact-audit` reports ok.
  Ruff now reports 49 findings in `ticket-driver/`, against 51 on the baseline; none are new.

## Frontier
Done on 2026-09-27. The corrected driver is measured in TJV-02.

Before this ticket: Ready. Evidence comes from the delivery-bench c3a arm: 31 of 42 runs gated, all on
fresh-judge `uncertain`. The local fix is authorized within the session goal of making c3a
complete the benchmark. This ticket makes no live model or Jev calls.

## Step-by-Step Implementation Plan
1. Write the RED tests: verdict parsing, the rendered prompt, the receipt in the review state,
   and the semantic retry both succeeding and persisting.
2. Derive the verdicts in `cascade.py` and render them into `prompts/judge.md`. Add the receipt
   to `state.review`.
3. Add the semantic retry in `driver.py`, reusing the directed-review retry mechanics.
4. Run the suites, the lint and the quick profile. Then review, open and merge the PR, and sync
   the installed skill.

## Testing Plan
Use the fake Pi leaf, the fake Jev and temporary repositories only. No hosted model or Jev.

## Out of Scope
- Question content, hashes and thresholds.
- The c\*b cycles, c4 and approval.
- Benchmark seeds, hidden suites and old receipts.
- Any benchmark run, which belongs to TJV-02.
