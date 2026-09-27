---
ticket_schema: 1
ticket_id: "TJV-02"
execution_mode: AFK
blocked_by: ["TJV-01", "TJV-03"]
---

# TJV-02 — Measure the corrected c3a on delivery-bench

## Artifact Graph
- Artifact ID: `artifact:ticket-driver-judge-verdicts-02`
- Role: `ticket`
- Parent: [ticket-driver-judge-verdicts.md](../../specs/ticket-driver-judge-verdicts.md)

## Parent Spec
[ticket-driver-judge-verdicts.md](../../specs/ticket-driver-judge-verdicts.md)

## What to Build
Open a new delivery-bench lot with only the `driver-c3a` arm. `prepare-drivers --source` copies
the TJV-01 driver from a clean checkout of its merge commit and records that commit and tree.
The benchmark does not change the global skill install. The lot binds the same three scenarios
with the same seed and suite digests as the original lot. Run it through chain length 8 under the protocol used for the other arms:
- 3 repetitions through request 3;
- at chain length 8, repetitions as the TBA-03 rule requires against the other arms' recorded
  results.

Judge what is still gated counterfactually and publish the comparison.

## Acceptance Criteria
- [x] A new lot records its authority, its driver copies bound to the TJV-01 merge commit, and seed
  and suite digests equal to the original lot's current digests. The original lot is never
  amended or rerun. (`c3a-observed`, authority sha256 `91af2cb0…`. The copies come from
  `8fa9ca6`, the TJV-03 merge, which contains TJV-01. Seeds, suites, canaries and model
  configuration were checked equal before the run. `db07-pilot` is untouched.)
- [x] c3a completes every requested cell with each request judged, and infrastructure failures
  are reported separately. (9 cells and 57 of 57 requests judged. There were 57 attempts, all
  `agent`, with no timeout and no audit hit. The stopped TJV-01 lot `c3a-verdicts` and its one
  unexplained driver exit are reported apart.)
- [x] The results report compares corrected c3a with the recorded arms at chain lengths 1, 3 and
  8. It covers acceptance, compass, cost and time, and gate reasons, and applies the TBA-03
  decision. It states the limits of a cross-lot comparison.
  ([delivery-bench-c3a-corrected.md](../../research/delivery-bench-c3a-corrected.md). TBA-03
  asked for repetition 2 at chain length 8, and it was run.)
- [x] Public documents hold no hidden check, trap or mechanism details. (Only counts, trap types
  and distances.)

## Frontier
Done on 2026-09-27. The first lot, `c3a-verdicts`, ran the TJV-01 driver. It was
stopped on purpose after 14 driver runs, once two judges were seen to lack their observations,
and it stays recorded as the TJV-01 measurement. The measured lot runs the TJV-03 driver. Model and Jev spend is authorized by the session goal of making c3a complete
the benchmark.

## Step-by-Step Implementation Plan
1. After TJV-01 is merged, run `init-lot`, `prepare-drivers --source` and a digest check
   against the original lot.
2. Run `run-lot --through 3` with 3 repetitions and `--through 8` for repetition 1, then
   `judge-gated`.
3. Apply TBA-03 against the recorded arms and add repetitions if required. Write the report and
   update the results document.

## Testing Plan
Run the harness unit tests before binding. The lot's own judge records are the evidence.

## Out of Scope
Changing scenarios, suites, other arms, or the original lot.
