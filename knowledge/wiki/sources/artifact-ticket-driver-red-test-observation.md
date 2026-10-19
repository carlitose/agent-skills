---
type: source
title: "Ticket-driver red-test observation: the end of each stream"
identity_key: artifact:ticket-driver-red-test-observation
identity_strength: stable
source_path: docs/specs/ticket-driver-red-test-observation.md
source_digest: sha256:ffff345b721f1288b33863986be952117d9c46118d0a0e8a1d567d3367fb637c
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-29
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Ticket-driver red-test observation: the end of each stream

Compiled from `docs/specs/ticket-driver-red-test-observation.md`. Identity is `artifact:ticket-driver-red-test-observation`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-29** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-ticket-driver-red-test-observation-rto-01]]
- Child source: [[sources/ticket-ticket-driver-red-test-observation-rto-02]]
- Child source: [[sources/ticket-ticket-driver-red-test-observation-rto-03]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-ticket-driver-red-test-observation.md","payload_bytes":3888,"payload_sha256":"ffff345b721f1288b33863986be952117d9c46118d0a0e8a1d567d3367fb637c"}],"payload_bytes":3888,"payload_sha256":"ffff345b721f1288b33863986be952117d9c46118d0a0e8a1d567d3367fb637c","schema":1,"source_digest":"sha256:ffff345b721f1288b33863986be952117d9c46118d0a0e8a1d567d3367fb637c","source_identity":"artifact:ticket-driver-red-test-observation","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":3888,"payload_sha256":"ffff345b721f1288b33863986be952117d9c46118d0a0e8a1d567d3367fb637c","schema":1,"source_digest":"sha256:ffff345b721f1288b33863986be952117d9c46118d0a0e8a1d567d3367fb637c","source_identity":"artifact:ticket-driver-red-test-observation"} -->
```markdown
# Ticket-driver red-test observation: the end of each stream

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-red-test-observation`
- Role: `spec`
- Standalone: true

### Children
- [RTO-01 — show the retry question the end of each stream](../tickets/ticket-driver-red-test-observation/done/01-show-the-end-of-each-stream.md)
- [RTO-02 — keep a verbose passing suite alive](../tickets/ticket-driver-red-test-observation/done/02-keep-a-verbose-suite-alive.md)
- [RTO-03 — give a mature suite time to finish](../tickets/ticket-driver-red-test-observation/done/03-give-a-mature-suite-time.md)

## Problem and evidence
The diagnosis in this section was incomplete; see [Correction](#correction-rto-02).

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

## Correction (RTO-02)
The diagnosis above was incomplete, and its count was wrong: 6 of the 15 gates, not 7, asked
`retry.recoverable`. The test receipts of all six end with `failure` `output-limit` and no exit
code. The capture killed the suite once its output passed the policy limit of 64 KiB. The output
ended mid-stream because the process was stopped there, so no verdict existed in either stream.
RTO-01 still keeps the verdict of a suite that completes visible, but it did not address those
gates.

The kill hit 17 of the 120 driver runs of lot `dbh`:
- 16 of the 18 crdt-yjs runs that reached the test step (the other 2 were genuinely red);
- 1 sql-engine run.

The crdt-yjs suite passes at its seed commit and prints about 87 KB, so no crdt-yjs candidate of
the drivers could integrate. RTO-02 raises the shipped limit to 8 MiB. It is covered by a RED
test in `ticket-driver/tests/test_driver.py`: a fake suite prints 128 KiB and passes.

## A slow suite killed as red tests (RTO-03)
The re-measure of the fixed drivers (lot `dbh-drivers`) found one more kill that the driver
counts as red tests. The shipped `test_timeout_seconds` was 180. In lot `dbh` the sql-engine suite
ran 71 to 136 s in the driver. In `dbh-drivers` four sql-engine cells ran at once, and 9 of 11
suite runs passed 180 s and were killed. RTO-03 raises the shipped timeout to 600 s, over four
times the slowest run alone.

```
