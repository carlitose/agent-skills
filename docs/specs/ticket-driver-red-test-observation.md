# Ticket-driver red-test observation: the end of each stream

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-red-test-observation`
- Role: `spec`
- Standalone: true

### Children
- [RTO-01 — show the retry question the end of each stream](../tickets/ticket-driver-red-test-observation/done/01-show-the-end-of-each-stream.md)

## Problem and evidence
In lot `dbh` of delivery-bench-hard (DBH-09, `openai-codex/gpt-6-luna` with medium thinking),
15 c3a runs stopped at the semantic gate. In 7 of them the uncertain question was
`retry.recoverable` after red tests. The fallback judge wrote that the captured output ends
mid-stream, with no failing test, assertion or exit cause, and answered undetermined.

The cause is in the driver. `driver.py` joined `stderr + stdout`, and `state.retry` kept the first
8192 characters. A build that writes many warnings to stderr fills that observation, so the
runner's verdict at the end of stdout never reaches Jev or the judge. The gate then asks a human
about output it never showed. Evidence: the `summary.json` of the gated runs in the private lot
records; only aggregates are published.

## Invariant
A red test run reaches `retry.recoverable` as the end of each stream: `stdout_tail` and
`stderr_tail`, 4096 characters each. A verdict at the end of either stream is visible, whatever
the other stream holds.

The following stay unchanged:
- question, thresholds, cascade order and gate policy;
- the other semantic states;
- the short failure text of the c1b stop path.

## Scope and verification
- Change `ticket-driver/scripts/state.py` (`red_tests`) and its call in `driver.py`.
- Add two causal tests in `ticket-driver/tests/test_c2.py`:
  - build noise on stderr, with the verdict at the end of stdout: RED on the baseline;
  - a verdict at the end of stderr, behind long stdout: a guard that the fix keeps it.
- Run all ticket-driver tests.

Out of scope:
- the `qa.evidence_class` gates (3 of the 15), which cite incomplete test sources, and the
  `review.*` gates, which judged the builder's content;
- the measured behavior of past lots, which ran without the fix.
