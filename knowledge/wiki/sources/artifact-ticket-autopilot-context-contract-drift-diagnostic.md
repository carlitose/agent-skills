---
type: source
title: "Ticket-Autopilot Context Contract Drift"
identity_key: artifact:ticket-autopilot-context-contract-drift-diagnostic
identity_strength: stable
source_path: docs/specs/ticket-autopilot-context-contract-drift-diagnostic.md
source_digest: sha256:fa0d53f3ecd777ca4328de1e8f88f23f7647b38fb64f215e0b4f464a7465d50c
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-08-29
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Ticket-Autopilot Context Contract Drift

Compiled from `docs/specs/ticket-autopilot-context-contract-drift-diagnostic.md`. Identity is `artifact:ticket-autopilot-context-contract-drift-diagnostic`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-08-29** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-ticket-autopilot-context-contract-drift-cb-01]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[],"status":"not-identified"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[],"status":"not-identified"},"invariants":{"headings":[],"status":"not-identified"},"verification":{"headings":[],"status":"not-identified"}},"parts":[{"index":0,"path":"wiki/sources/artifact-ticket-autopilot-context-contract-drift-diagnostic.md","payload_bytes":5623,"payload_sha256":"fa0d53f3ecd777ca4328de1e8f88f23f7647b38fb64f215e0b4f464a7465d50c"}],"payload_bytes":5623,"payload_sha256":"fa0d53f3ecd777ca4328de1e8f88f23f7647b38fb64f215e0b4f464a7465d50c","schema":1,"source_digest":"sha256:fa0d53f3ecd777ca4328de1e8f88f23f7647b38fb64f215e0b4f464a7465d50c","source_identity":"artifact:ticket-autopilot-context-contract-drift-diagnostic","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | no matching section identified in the source; complete source retained |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | no matching section identified in the source; complete source retained |
| invariants | no matching section identified in the source; complete source retained |
| verification | no matching section identified in the source; complete source retained |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":5623,"payload_sha256":"fa0d53f3ecd777ca4328de1e8f88f23f7647b38fb64f215e0b4f464a7465d50c","schema":1,"source_digest":"sha256:fa0d53f3ecd777ca4328de1e8f88f23f7647b38fb64f215e0b4f464a7465d50c","source_identity":"artifact:ticket-autopilot-context-contract-drift-diagnostic"} -->
````markdown
# Ticket-Autopilot Context Contract Drift

## Artifact Graph

- Artifact ID: `artifact:ticket-autopilot-context-contract-drift-diagnostic`
- Role: `spec`
- Standalone: true

### Children

- [CB-01 compact the runner contract within the existing context ceiling](../tickets/ticket-autopilot-context-contract-drift/done/01-compact-runner-contract-within-ceiling.md)

## Type

Diagnostic spec

## Status

Fixed by CB-01; verified within the unchanged ceiling.

## Diagnosis Report - lens: recent-change

### Root cause

The ticket-autopilot workflow contract grew across the leaf-budget, reconciliation-target,
and wiki-sync tickets, but its governed context surfaces were not reconciled as one atomic
change. Since the last green TK-04 baseline, `ticket-autopilot/SKILL.md` is the only static
closure source whose bytes changed. It grew from 10,328 to 11,523 normalized bytes and from
120 to 133 lines. That single 1,195-byte increase explains the workflow closure moving from
53,346 to 54,541 bytes and the composed total moving from 166,001 to 167,196 bytes.

The existing ceiling is 166,002 bytes, so the current contract exceeds it by 1,194 bytes.
The skill also exceeds its independent 130-line concision limit by three lines. The baseline
test is not wrong to fail: its exact values are the drift detector. The integration defect is
that feature tickets added valid instructions and partially refreshed the operator guide, but
neither compacted the contract back under the existing ceiling nor performed an explicitly
authorized ceiling raise with synchronized tests and rationale.

### Evidence

- `test_repository_baseline_reproduces_the_autopilot_inventory` fails first at workflow
  closure words: `6,937` expected, `7,098` observed.
- The same controlled report observes closure `54,541`, composed total `167,196`, configured
  ceiling `166,002`, status `exceeded`, and delta `1,194`.
- `test_skill_docs_are_concise` observes 133 lines against a 130-line limit.
- Comparing all eleven closure sources from baseline `a9b9f51c` to current `main` shows only
  `ticket-autopilot/SKILL.md` changed: 21 insertions and 8 deletions.
- The skill's measured history is: 10,328 bytes/120 lines at TK-04; 10,809/130 after LB-01;
  10,538/128 after RT-01; 11,057/130 after the WS-04 seal; and 11,523/133 after WS-06.
- `docs/autopilot-context-cost-guide.md` was updated to the current 54,541-byte closure and
  59,540-byte static prefix, proving the measurement was known, while the baseline test and
  ceiling contract stayed at their earlier values.

### Feedback loop built

Run the two repository tests and the controlled measurement:

```bash
python3 -B -m unittest \
  ticket-autopilot.tests.test_context_budget.ContextBudgetTests.test_repository_baseline_reproduces_the_autopilot_inventory \
  ticket-autopilot.tests.test_skill_graph.SkillGraphTests.test_skill_docs_are_concise -v
```

The tests fail with the exact closure and line-count signals above. The controlled
`measure_context_budget(..., workflow="ticket-autopilot")` report independently returns
`status: exceeded` and `delta_bytes: 1194`.

### Fix location and approach

Apply behavior-preserving document simplification to `ticket-autopilot/SKILL.md`. Preserve
every current authority, lifecycle, verification, reconciliation, delivery, wiki-sync, and
failure contract, but consolidate repetition and route details to the existing versioned
references. Reduce the workflow closure by at least 1,195 bytes and the skill to at most 130
lines so the composed total is within the unchanged 166,002-byte ceiling.

After freezing the compacted skill, regenerate the exact controlled word/byte totals and
update `test_context_budget.py` plus `docs/autopilot-context-cost-guide.md` to those observed
values. Keep the ceiling value unchanged. Run skill-graph, context-budget, policy, full runner,
and instruction-boundary tests to prove that compaction did not remove required behavior.

### Alternatives ruled out

- **Raise the ceiling to the current total.** Rejected without an explicit budget decision:
  it would convert a guard failure into accepted permanent context cost and hide the missing
  compaction step.
- **Update only the exact test numbers.** Rejected: the report would still say
  `status: exceeded`, so the workflow would remain outside its declared budget.
- **Remove the recent leaf-budget, reconciliation, or wiki-sync contracts.** Rejected: those
  instructions correspond to shipped runner behavior and tested safety boundaries.
- **Change the measurement algorithm or exclude `ticket-autopilot/SKILL.md`.** Rejected: the
  skill is necessarily part of the workflow static closure, and the one-file byte delta
  already explains the entire breach.
- **Treat the 133-line failure as unrelated formatting.** Rejected: both failures originate
  in the same document growth, and one coherent compaction fixes both without semantic drift.

### Confidence: high

The exact byte delta, line history, closure-source comparison, guide history, and two failing
tests all identify the same unreconciled contract-growth mechanism.

## Fix Verification

CB-01 compacted `ticket-autopilot/SKILL.md` without changing executable runner behavior or
the ceiling configuration. The skill now measures 10,230 bytes, 1,240 words, and 102 lines.
The controlled workflow report measures a 4,999-byte listing, 53,248-byte closure,
58,247-byte static prefix, and 165,903-byte worst-case composed total against the unchanged
166,002-byte ceiling (`status: within`, 99 bytes of headroom). The exact baseline assertions
and operator guide now quote those same values.

````
