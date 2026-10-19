---
type: source
title: "Ticket-driver QA observation: what the evidence question sees"
identity_key: artifact:ticket-driver-qa-observation
identity_strength: stable
source_path: docs/specs/ticket-driver-qa-observation.md
source_digest: sha256:b79d99f8ca7e92bbc14ce697503f1c13371bc7138d3e527e00e3d58814ebf7f1
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-29
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Ticket-driver QA observation: what the evidence question sees

Compiled from `docs/specs/ticket-driver-qa-observation.md`. Identity is `artifact:ticket-driver-qa-observation`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-29** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-ticket-driver-qa-observation-qao-01]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-ticket-driver-qa-observation.md","payload_bytes":2282,"payload_sha256":"b79d99f8ca7e92bbc14ce697503f1c13371bc7138d3e527e00e3d58814ebf7f1"}],"payload_bytes":2282,"payload_sha256":"b79d99f8ca7e92bbc14ce697503f1c13371bc7138d3e527e00e3d58814ebf7f1","schema":1,"source_digest":"sha256:b79d99f8ca7e92bbc14ce697503f1c13371bc7138d3e527e00e3d58814ebf7f1","source_identity":"artifact:ticket-driver-qa-observation","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":2282,"payload_sha256":"b79d99f8ca7e92bbc14ce697503f1c13371bc7138d3e527e00e3d58814ebf7f1","schema":1,"source_digest":"sha256:b79d99f8ca7e92bbc14ce697503f1c13371bc7138d3e527e00e3d58814ebf7f1","source_identity":"artifact:ticket-driver-qa-observation"} -->
```markdown
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

```
