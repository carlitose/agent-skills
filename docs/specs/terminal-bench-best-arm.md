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
- [TBA-06](../tickets/terminal-bench-best-arm/done/06-generic-driver-arms.md)
- [TBA-07](../tickets/terminal-bench-best-arm/07-run-driver-lots.md)

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
2. **Candidate arms (updated 2026-09-26):** all four. Pi bare (lot B) and skills-only (the same frozen TBF-05 snapshot in the system prompt) as before. After the user objected that only Pi bare had been tried («I bracci ! non hai provato un cazzo») and chose «Costruisci c1a/c3a generici», c1a and c3a return in a **generic** form that needs no task-specific check (see *Generic ticket-driver arms*). Every arm still exposes only `sandbox_exec` to the model and runs on unchanged original tasks and verifiers.
3. **Winner rule:** paired comparison per task on the same task list, with verified reward as the only score. An exception with no verifier decision counts as a failure for the arm, and its count is reported. If the pass-count difference is at most 3 tasks, or a McNemar exact test gives p ≥ 0.05, run one more repetition of the arms concerned before deciding. With four arms, compare each arm with Pi bare pairwise under this rule (Holm correction across the three comparisons). If the result is still indistinguishable, choose the simpler arm (order: Pi bare, skills-only, c1a, c3a). Report cost, requests and time as secondary measures, never as the score.
4. **Development protocol:** before any change, split the 63 tasks deterministically into **dev (42)** and **held-out (21)**, ordered by SHA-256 of the task name; the split file is committed. Changes to the winner (system prompt, skill content, sandbox tool ergonomics, stop and verification habits) may be driven only by dev trajectories and dev verifier outcomes. Held-out verifier logs are not read before the final measurement. A change is accepted only when it improves dev without regressing on a fresh held-out run, and the final claim cites held-out and full 63-task results separately from the lots used to develop it.
5. **Own benchmark:** not needed to obtain a score, because the original harness works. It is kept as a **conditional slice**: a private set of Terminal-Bench-style Harbor tasks from our own domain, used either if the original harness becomes unusable, or as a contamination-free held-out for development. Building it requires an explicit user go-ahead on scope (number of tasks, domains).

## Generic ticket-driver arms

The TBF-05 c1a/c3a relied on a hand-written public smoke per task and a Git fingerprint, and they discarded the candidate when the gate failed. Neither is possible or useful on 63 arbitrary original tasks, so the generic arms keep the driver idea (independent checking, typed judgment, one bounded correction) without task-specific code or Git:

- **Builder:** the same phase as skills-only: the original instruction unchanged, with the frozen skills snapshot in the system prompt.
- **Checker (c1a and c3a):** a fresh Pi session with no builder history. It receives the original instruction, derives acceptance checks from it, runs them through `sandbox_exec` without modifying deliverables (scratch files only under `/tmp`, an instruction-level rule), and ends with `VERDICT: PASS` or `VERDICT: FAIL` plus the failing criteria and evidence.
- **c1a decision:** if the verdict is not `PASS`, one **corrector** phase (fresh session, builder system prompt) receives the instruction and the checker report and fixes the reported failures. There is no second correction and no rollback: the candidate always reaches Harbor's verifier.
- **c3a adds:** a fresh read-only **reviewer** that inspects the deliverables against the instruction and reports `[blocker]`/`[should-fix]` findings or `No findings.`; then host-only **Jev** typed judgments (`review.findings_block`, `review.scope_complete`, `verify.claim_supported`) over the instruction, the checker report and the review, classified by the existing arbiter policy. A correction runs when any judgment is not the approving answer or the checker did not pass. If Jev fails or is uncertain, the decision falls back to the checker verdict plus the reviewer's `[blocker]` markers, and the fallback is recorded. Jev state fields are truncated with explicit markers to stay within the 24 KiB request bound that stopped two TBF-05 c3a cells.
- The Jev key stays host-only (`jev_key_scope`), never reaches Pi or a container, and was copied to the benchmark host with the user's explicit consent («Sì, copia e usa Jev»). Jev usage is journaled and added to the cell's estimated cost.
- The bridge enforces the phase grammar: builder first with the unchanged instruction; then `checker`, `reviewer` (c3a only) and at most one `corrector`, each once and in that order. Every prompt contains the original instruction verbatim, and the system prompts are fixed constants (the corrector's equals the builder's).

These are deviations from the original ticket-driver, reported as such, and not a reproduction of it.

## Invariants
- Task images, instructions, resources, timeouts and verifiers stay original; no hidden test or solution is opened. Verifier logs are read only for dev tasks.
- Each lot has its own external lot file, authority text and ledger. Every start is recorded, there are no retries within a lot, and the lots are never mixed or cherry-picked.
- Credentials stay on the host; Pi exposes only `sandbox_exec`; any arm-specific context is a frozen, hashed snapshot.
- No leaderboard submission and no claim of official parity: results are "our Pi on the original tasks, 63/66".

## Slices
- **TBA-01:** add the skills-only arm to the original adapter: arm option, frozen snapshot bound by SHA-256 in the lot file, snapshot appended to the system prompt, Pi bare unchanged. Test-first, CI, merge.
- **TBA-02:** run the skills-only lot on the lot B task list with the same policy, after lot B finishes, with no overlapping containers.
- **TBA-03:** paired selection report across the four arms (and a second repetition of both arms if the rule requires it), committing the winner and the dev/held-out split.
- **TBA-04:** develop the winner on dev: failure taxonomy from trajectories, small targeted changes, dev re-runs, then one held-out and one full confirmation run, with a report.
- **TBA-06:** implement the generic c1a/c3a arms on the original adapter, test-first; CI and merge.
- **TBA-07:** run one 63-task lot for c1a and one for c3a, serially after skills-only, with infrastructure retries.
- **TBA-05 (conditional):** private Terminal-Bench-style task set in Harbor format, only on explicit user go-ahead.

## Verification strategy
Offline unit tests for arm binding and snapshot drift (TBA-01); a live Harbor install-only check before paid-free starts; per-lot ledger, receipts and Harbor `result.json` for every cell; McNemar computed from the paired table in the report; held-out isolation checked by listing which verifier logs were read. Live results are observations of one or two repetitions and are reported with their counts.

## Open questions
- The development budget in lots, or when to stop improving. Default: stop after three dev iterations with no gain above 2 tasks.
- Whether to add a second model later. Out of scope here.
