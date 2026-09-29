# Ticket-driver QA observation: what the evidence question sees

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-qa-observation`
- Role: `spec`
- Standalone: true

### Children
- [QAO-01 — show the evidence question the suite's end and its test folder](../tickets/ticket-driver-qa-observation/done/01-show-the-suite-end-and-test-folder.md)

## Problem and evidence
In lot `dbh` of delivery-bench-hard (DBH-09, `openai-codex/gpt-6-luna` with medium thinking),
3 of the 15 c3a gates asked `qa.evidence_class`. Each time the fallback judge answered
undetermined.
- **2 on lua-vm**: the state had no test sources. The judges wrote that the state gives no
  test-source paths. Lua keeps its suite in `testes/`, and the driver's path convention
  (`TEST_PATH` in `driver.py`) did not count that folder.
- **1 on sql-engine**: the sources were the first test files in path order, and one large file
  filled the budget. The judge wrote that the source capture was incomplete.

A third gap has not gated yet. `state.qa` keeps the first 8192 characters of `stdout + stderr`.
Since RTO-02 raised the capture limit, a verbose suite that passes reaches this question, and
the head of its output is build noise. The suite's verdict comes last. The other states
(`observed`, `red_tests`) already read the end.

## Invariant
- The evidence question sees the end of each stream, `stdout_tail` and `stderr_tail`, 4096
  characters each, as for red tests.
- A `testes/` folder holds tests, like `test/` and `tests/`.

The following stay unchanged:
- the question, its classes, thresholds and gate policy;
- the order and budget of the test sources;
- the other states.

## Scope and verification
- Change `state.qa` and `TEST_PATH` in `driver.py`.
- Add two causal tests in `ticket-driver/tests/test_verdicts.py`, both RED on the baseline:
  - a verbose suite's verdict, at the end of stdout, and the end of stderr reach the state;
  - `testes/all.lua` is a test source.
- Run all ticket-driver tests.

Out of scope:
- the sql-engine gate: choosing which sources to show is a separate design question;
- whether a gate should wait for a human when one class of a large mature suite cannot be
  decided. That is gate policy, a proposal for the user;
- past lots, which ran without the fix.
