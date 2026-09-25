# TBF-05 — Modified Git-overlay comparison (terminal report)

**Scope:** 12/12 authorized starts, three frozen tasks × four adapted arms, in series, no retries. Execution code HEAD `add93366cbab9811f8ae2fce1f497505730cc8f1`; its required exact-head CI [passed](https://github.com/carlitose/agent-skills/actions/runs/36064405307). These are **local modified-harness** observations, not standard Terminal-Bench leaderboard scores or a faithful invocation of the original ticket-driver. Harbor's original separate verifier ran only where the table has a numeric reward. `—` means **no verifier decision**, not zero.

| Task | Arm | Harbor reward | Estimated USD incl. Jev | Pi requests | Jev requests | Local gate / outcome |
|---|---|---:|---:|---:|---:|---|
| html-js-filter | Pi bare | 0 | 0.2240192 | 11 | 0 | No added gate |
| html-js-filter | skills-only | 0 | 0.2615796 | 19 | 0 | No added gate |
| html-js-filter | adapted c1a | 0 | 0.2534268 | 13 | 0 | Public smoke passed; verifier failed |
| html-js-filter | adapted c3a | — | 0.2779648 | 17 | 0 | Jev pre-request failure; verifier not run |
| interleaved-vigenere | Pi bare | 0 | 0.2134728 | 18 | 0 | No added gate |
| interleaved-vigenere | skills-only | **1** | 0.3643436 | 27 | 0 | No added gate |
| interleaved-vigenere | adapted c1a | 0 | 0.4035336 | 26 | 0 | Public smoke passed; verifier failed |
| interleaved-vigenere | adapted c3a | 0 | 0.467860252 | 33 | 4 | Semantic gate failed; candidate discarded before verifier |
| wal-recovery-ordering | Pi bare | 0 | 0.2439716 | 18 | 0 | No added gate |
| wal-recovery-ordering | skills-only | 0 | 0.2427048 | 16 | 0 | No added gate |
| wal-recovery-ordering | adapted c1a | 0 | 0.2367956 | 20 | 0 | Public smoke passed; verifier failed |
| wal-recovery-ordering | adapted c3a | — | 0.2166112 | 18 | 0 | Jev pre-request failure; verifier not run |

**Totals (estimated, not invoices):** Pi bare $0.6814636 (0/3 verified passes); skills-only $0.868628 (1/3); adapted c1a $0.893756 (0/3); adapted c3a $0.962436252 (0/1 verifier decisions, **2 without a decision**). All 12 starts: **$3.406283852**, including **$0.000176652** for Jev's reported input usage in the one c3a cell that made four requests. Remaining within the modified $720 estimated lot: $716.593716148. Every modified-cell cost estimate was reconciled to an attributable model journal; both c3a errors have known model estimates and **zero Jev requests**, not unknown cost. The ledger is closed at 12/12, unblocked and without pending starts.

**Failures and limits:** Two c3a starts ended with `JevFailure` before a verifier run. Their host-only Jev journals each contain an initial and failure event with zero requests; Pi host processes stopped and model journals accounted for their tokens. Offline reconstruction of each *public* candidate artifact found a first risk-judgment payload of 24,693 bytes (HTML) and 24,751 bytes (WAL), exceeding the frozen 24,576-byte pre-request bound by 117 and 175 bytes respectively. This is evidence for the pre-request failures, not a claim that either task failed its verifier. The interleaved c3a cell made four attributable Jev requests, but its semantic gate discarded the candidate, yielding verifier reward 0. All three c1a public smokes passed yet all three verifier rewards were 0: these smoke checks are explicitly non-exhaustive. This three-task, single-start-per-cell sample is not a statistically supported ranking; do not extrapolate the lone skills-only success or compare it as a leaderboard equivalent.

**Attribution:** The outside-Git ledger at `C:/Users/rdpuser/projects/.tbf-env/modified-comparison-live/ledger.jsonl` has SHA-256 `6ae0764ffc7978f6427e5b23d315bfa3d9085036370e4fc75269008ad7ea13a8`; binding SHA-256 `29a537c8263e4bd99f8fb9529e1d320fa64381e1fb70f772d09f31cc7f46ad99`. All 12 Harbor `result.json` and agent journals remain under that directory's `trials/`, not in Git. Task checksum is identical across the four cells of each task. Each verifier decision, model/Jev journal, ledger settlement and host termination was checked individually; the report is a derived snapshot, not a substitute for those receipts. No hidden tests or solutions were opened for this report.

**Separate standard pilot:** The original, non-overlay TBF-03 consumed 3/3 starts with one verifier reward 0 and model estimate $0.1765772, then two starts with **unknown actual costs and no verifier decisions**. Each failed start's $60 was a separate *admission assumption only*, not observed spending. Its immutable ledger SHA-256 is `ce4b46c78577f7c80511aa0b612380ca6fb5051a1228441a5b26c0d470d82688`. Do not add these unknown costs to the modified $3.406283852 estimate as though measured. No additional start, retry or merge is authorized by this report.
