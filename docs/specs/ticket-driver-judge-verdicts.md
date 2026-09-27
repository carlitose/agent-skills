# Ticket-driver judge verdicts: a decidable answer for every escalated question

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-judge-verdicts`
- Role: `spec`
- Standalone: true

### Children
- [TJV-01 — give the fresh judge a decidable verdict and the driver's test receipt](../tickets/ticket-driver-judge-verdicts/done/01-decidable-judge-verdicts.md)
- [TJV-02 — measure the corrected c3a on delivery-bench](../tickets/ticket-driver-judge-verdicts/02-measure-corrected-c3a.md)

## Problem and evidence
Bug analysis. In the delivery-bench measurement ([results](../research/delivery-bench-results.md))
c3a stopped at a human gate in 31 of its 42 runs. The benchmark runs AFK, with no human. Each gate
left its request undelivered, and the next request started from a main branch without it. All 31
gates came from a fresh-judge escalation whose prose the driver parsed as `uncertain`. None came
from a decisive negative answer. There are three defects, largest first:

1. **`qa.evidence_class` can never be decided by the fresh judge.** `prompts/judge.md` suggests
   decisive sentences for three questions and none for this one. `_judge_answer` looks for the
   literal `<class> test`, which the prompt never asks the judge to write. The result was
   uncertain in 15 of 15 escalations, and each one gated. bench38 hid the defect: Python
   `unittest` output lets Jev answer `unit` without escalating. The C and TypeScript scenarios run
   unit binaries together with CLI or browser checks. There Jev's distribution splits and the
   question always escalates.
2. **The fast lane only recognises the sample sentences, anywhere in the prose.** Of the 16
   uncertain escalations on the two review questions, 6 held a decisive answer in other words:
   5 negatives (a concrete unmet criterion) and 1 "no blocking defect". One used the
   `findings_block` sentence to answer `scope_complete`. Matching anywhere also accepts a quoted
   sentence as the verdict, so a judge that cites the review's "No findings." before disagreeing
   produces a false pass. `retry.recoverable` defines an `environment-failure` answer that the
   parser can never return.
3. **The review state has no driver-observed test result.** The judge receives the task, the diff
   and the review prose. The scope question forbids relying on a self-declared pass, yet the
   driver's own test receipt, which is not self-declared, is left out. In 8 of the 16 uncertain
   review escalations the judge's only reason was the missing test evidence.

A decisive review negative (a blocker, or a criterion with no implementation path) opens the
same human gate as uncertainty. AFK has no one to answer it. A directed-review blocker already
reenters one bounded builder retry; a semantic review negative does not.

The stopped work was mostly good. Gated runs started from a clean base, where every earlier
request was integrated: in 8 of 8 the hidden judge counterfactually accepted the candidate. It
also accepted 10 of the 11 integrated runs.

## TJV-01 invariants
1. **The question registry defines the verdict.** For the question asked, the judge prompt lists
   the criteria and one `Answer: <value>` line per allowed value: `yes`/`no` for `noul` (criteria
   `true`/`false`), each criteria key for `choice`, plus `Answer: undetermined`. The driver
   accepts a verdict only if exactly one `Answer:` line exists, it is the last non-empty line and
   its value is allowed. Anything else is `uncertain` and gates as before: no line, several lines,
   a line that is not last, an unknown value, `undetermined`, or an unavailable judge. Sentences
   are no longer matched anywhere in the prose.
2. **The review state carries the driver-observed test receipt**: argv, exit code and a bounded
   output tail, named as driver-observed. The judge prompt says that driver-observed fields are
   not builder claims. The QA and verify states are unchanged.
3. **A decisive review negative reenters the one builder retry, for c2a and c3a only.**
   A negative is `review.findings_block=yes` or `review.scope_complete=no`. It triggers the retry
   only while the run's single builder retry is unused. The retry passes the finding to the
   builder: the judge's prose when the question escalated, otherwise the question and Jev's
   decision. Builder 2 is followed by the mandatory test command, the byte-identical candidate
   check and the semantic gates again. The budget is shared with the directed-review retry. Once
   it is spent, a negative gates as before. Uncertainty never triggers a retry and never becomes
   `yes`.
4. **Unchanged:**
   - `questions/*.json` and their hashes, Jev thresholds, cascade order, and one judge per
     question per gate pass;
   - Jev key isolation, approval and resume;
   - the c1/c\*b cycles and c4.

## Scope and verification
Change `ticket-driver/scripts/cascade.py`, `driver.py`, `state.py`, `prompts/judge.md` and the
tests and fakes. Each test must fail on the baseline:
- a judge ending with `Answer: integration` for `qa.evidence_class` still gates;
- a judge quoting "No findings." and ending with a negative verdict passes;
- the review judge's prompt lacks the test receipt;
- a decisive scope negative in c3a gates without a retry.

After the change, all of these must be green: the new tests, every ticket-driver suite, ruff,
the file-limit lint and the local quick profile. The old c3a results stay recorded as the
measurement of the uncorrected driver. They are never amended or rerun. TJV-02 measures the
corrected driver in a new lot.
