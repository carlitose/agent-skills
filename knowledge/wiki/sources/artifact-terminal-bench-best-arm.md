---
type: source
title: "Terminal-Bench — scegliere il braccio migliore e svilupparlo"
identity_key: artifact:terminal-bench-best-arm
identity_strength: stable
source_path: docs/specs/terminal-bench-best-arm.md
source_digest: sha256:6042fa5bc6d2ce3e6488286da34fc2ceddf2db600da44370f3f884d6a63ff5a3
source_status: present
artefact_kind: spec
disposition: not-applicable
created: 2026-09-25
created_provenance: git-commit
disposition_changed:
disposition_changed_provenance: unknown
---

# Terminal-Bench — scegliere il braccio migliore e svilupparlo

Compiled from `docs/specs/terminal-bench-best-arm.md`. Identity is `artifact:terminal-bench-best-arm`, which is why moving the artefact between dispositions updates this page instead of creating a second one.

## Dates

- Created: **2026-09-25** via `git-commit`
- Disposition changed: **unknown** — no rung produced a date

## Graph

- Child source: [[sources/ticket-terminal-bench-best-arm-tba-01]]
- Child source: [[sources/ticket-terminal-bench-best-arm-tba-02]]
- Child source: [[sources/ticket-terminal-bench-best-arm-tba-03]]
- Child source: [[sources/ticket-terminal-bench-best-arm-tba-04]]
- Child source: [[sources/ticket-terminal-bench-best-arm-tba-05]]

## Semantic coverage

<!-- semantic-projection-v1: {"coverage":{"decisions":{"headings":[6],"status":"present"},"exclusions":{"headings":[],"status":"not-identified"},"goals":{"headings":[4],"status":"present"},"invariants":{"headings":[7],"status":"present"},"verification":{"headings":[9],"status":"present"}},"parts":[{"index":0,"path":"wiki/sources/artifact-terminal-bench-best-arm.md","payload_bytes":6618,"payload_sha256":"6042fa5bc6d2ce3e6488286da34fc2ceddf2db600da44370f3f884d6a63ff5a3"}],"payload_bytes":6618,"payload_sha256":"6042fa5bc6d2ce3e6488286da34fc2ceddf2db600da44370f3f884d6a63ff5a3","schema":1,"source_digest":"sha256:6042fa5bc6d2ce3e6488286da34fc2ceddf2db600da44370f3f884d6a63ff5a3","source_identity":"artifact:terminal-bench-best-arm","source_kind":"spec"} -->

| Topic | Source sections |
|---|---|
| goals | 4: Goal |
| exclusions | no matching section identified in the source; complete source retained |
| decisions | 6: Decisions |
| invariants | 7: Invariants |
| verification | 9: Verification strategy |

## Preserved source

Literal source text; not an agent-authored summary.

<!-- semantic-payload-v1: {"part_index":0,"payload_bytes":6618,"payload_sha256":"6042fa5bc6d2ce3e6488286da34fc2ceddf2db600da44370f3f884d6a63ff5a3","schema":1,"source_digest":"sha256:6042fa5bc6d2ce3e6488286da34fc2ceddf2db600da44370f3f884d6a63ff5a3","source_identity":"artifact:terminal-bench-best-arm"} -->
```markdown
# Terminal-Bench — scegliere il braccio migliore e svilupparlo

## Artifact Graph
- Artifact ID: `artifact:terminal-bench-best-arm`
- Role: `spec`
- Standalone: true

### Children
- [TBA-01](../tickets/terminal-bench-best-arm/done/01-add-skills-only-arm.md)
- [TBA-02](../tickets/terminal-bench-best-arm/02-run-skills-only-lot.md)
- [TBA-03](../tickets/terminal-bench-best-arm/03-select-the-winner.md)
- [TBA-04](../tickets/terminal-bench-best-arm/04-develop-the-winner.md)
- [TBA-05](../tickets/terminal-bench-best-arm/05-private-benchmark.md)

## Type and status
Decision and feature specification. Draft, 2026-09-25. It builds on [Terminal-Bench 4.0 pilot and full lot](terminal-bench-4-opus55.md) and reuses its original-task adapter, frozen manifest and flat-rate lot policy. No new spending rule: the user stated that tokens are flat-rate («supera tutti i budget tanto ho token flat»). USD figures stay estimates, not invoices.

## Goal
The user asked to «fare uscire il braccio migliore e svilupparlo», and, if Terminal-Bench did not work, to build a similar benchmark of our own. The goal is one agent configuration (arm), chosen on the original Terminal-Bench 4.0 tasks with a paired and reproducible comparison, then improved without fitting the benchmark itself.

## Facts
- The four arms (Pi bare, skills-only, adapted c1a, adapted c3a) were only compared in TBF-05: 3 tasks, one start per cell, **modified** Git-overlay harness. Skills-only passed 1/3, the others 0/3, and two c3a cells had no verifier decision. The report itself says the sample supports no ranking.
- In TBF-05 all three c1a public smoke checks passed while the original verifier failed, so the driver's check stage did not predict success. c1a/c3a need Git and task-specific public checks written by hand for each task; those exist only for the three pilot tasks.
- The original harness now works for Pi bare. Adapter `standard_full:FullStandardPiHarborAgent` runs unchanged tasks, verifies after agent failures and supports a declared flat-rate policy (PR #348, #349). Lot B (Pi bare, 63 CPU tasks, 1,000 requests per start, `-n 3`) is running; its first verified results were 2 passes out of 5.
- The skills-only snapshot used in TBF-05 is `benchmarks/terminal-bench-4-opus55/comparison-skills.md` (sha256 `cfda572172516a40b188f31ac5e8eb77c41ae2672458b0fb9e5039b235173c42`, 7 skills).

## Decisions
1. **Selection harness:** the original Terminal-Bench 4.0 tasks through the TBF-06 adapter: the same 63 CPU tasks, GPU tasks excluded as lost coverage, and the same model, reasoning, flat-rate agent policy and concurrency as lot B. Results from the modified harness never enter the selection.
2. **Candidate arms:** Pi bare (lot B is its first repetition) and skills-only (the same frozen TBF-05 snapshot in the system prompt, and still only `sandbox_exec`). c1a and c3a are **not candidates** on this harness: no task-agnostic check exists, and hand-written checks for 63 tasks would amount to building a new benchmark. They return only through a separate spec with a generic check.
3. **Winner rule:** paired comparison per task on the same task list, with verified reward as the only score. An exception with no verifier decision counts as a failure for the arm, and its count is reported. If the pass-count difference is at most 3 tasks, or a McNemar exact test gives p ≥ 0.05, run one more repetition of **both** arms before deciding. If the result is still indistinguishable, choose the simpler arm (Pi bare). Report cost, requests and time as secondary measures, never as the score.
4. **Development protocol:** before any change, split the 63 tasks deterministically into **dev (42)** and **held-out (21)**, ordered by SHA-256 of the task name; the split file is committed. Changes to the winner (system prompt, skill content, sandbox tool ergonomics, stop and verification habits) may be driven only by dev trajectories and dev verifier outcomes. Held-out verifier logs are not read before the final measurement. A change is accepted only when it improves dev without regressing on a fresh held-out run, and the final claim cites held-out and full 63-task results separately from the lots used to develop it.
5. **Own benchmark:** not needed to obtain a score, because the original harness works. It is kept as a **conditional slice**: a private set of Terminal-Bench-style Harbor tasks from our own domain, used either if the original harness becomes unusable, or as a contamination-free held-out for development. Building it requires an explicit user go-ahead on scope (number of tasks, domains).

## Invariants
- Task images, instructions, resources, timeouts and verifiers stay original; no hidden test or solution is opened. Verifier logs are read only for dev tasks.
- Each lot has its own external lot file, authority text and ledger. Every start is recorded, there are no retries within a lot, and the lots are never mixed or cherry-picked.
- Credentials stay on the host; Pi exposes only `sandbox_exec`; any arm-specific context is a frozen, hashed snapshot.
- No leaderboard submission and no claim of official parity: results are "our Pi on the original tasks, 63/66".

## Slices
- **TBA-01:** add the skills-only arm to the original adapter: arm option, frozen snapshot bound by SHA-256 in the lot file, snapshot appended to the system prompt, Pi bare unchanged. Test-first, CI, merge.
- **TBA-02:** run the skills-only lot on the lot B task list with the same policy, after lot B finishes, with no overlapping containers.
- **TBA-03:** paired selection report (and a second repetition of both arms if the rule requires it), committing the winner and the dev/held-out split.
- **TBA-04:** develop the winner on dev: failure taxonomy from trajectories, small targeted changes, dev re-runs, then one held-out and one full confirmation run, with a report.
- **TBA-05 (conditional):** private Terminal-Bench-style task set in Harbor format, only on explicit user go-ahead.

## Verification strategy
Offline unit tests for arm binding and snapshot drift (TBA-01); a live Harbor install-only check before paid-free starts; per-lot ledger, receipts and Harbor `result.json` for every cell; McNemar computed from the paired table in the report; held-out isolation checked by listing which verifier logs were read. Live results are observations of one or two repetitions and are reported with their counts.

## Open questions
- The development budget in lots, or when to stop improving. Default: stop after three dev iterations with no gain above 2 tasks.
- Whether to add a second model later. Out of scope here.

```
