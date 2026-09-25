# Terminal-Bench 4.0 original tasks — Pi bare, full CPU lot (TBF-04)

**Result: 15/63 scored tasks passed (23.8%)** on the original Terminal-Bench 4.0 tasks with our Pi bare agent (`openai-codex/gpt-6-sol`, reasoning `high`), one repetition, through the native Harbor adapter of [TBF-06](../../docs/tickets/terminal-bench-4-opus55/done/06-adapt-original-harbor-to-pi.md). Original task images, instructions, resources, timeouts and separate verifiers; Harbor's verifier is the only score source. This is a **partial** run: 63 of 66 tasks, and not a leaderboard submission.

## Scope and method

- Dataset `terminal-bench/terminal-bench@sha256:39d9f44b40420cde8fdcc087579c0d72a7e14fa3656d603c3f0d22fb35e27732` (66 tasks, [frozen manifest](manifest.json)). Excluded as **lost coverage**, never replaced: `fp8-rmsnorm-gemm`, `jax-speedrun-gpu`, `math-eval-grader` (GPU).
- Mandate: the user's explicit choice «Sì, 63 task $150», then «supera tutti i budget tanto ho token falt» (flat-rate tokens). The per-start policy was therefore 1,000 model requests and a $9,000 estimated safety ceiling; USD figures are **estimates, not invoices**.
- Local Docker Desktop on the operator's Windows host (22 CPUs, 15.3 GiB VM), Harbor 0.23.0, `-n 3` (retry lot `-n 2`), `-k 1`, Harbor `--max-retries 0`.
- Infrastructure failures were repeated under the user's rule («se l'agente sbaglia è un conto, se fallisce per crash del harness di valutazione, per altri fattori che non sia fallimento del lavoro del agente allora è da ripete»); see [the adapter notes](standard-full.md#infrastructure-failures-are-repeated). Each cell reports its first non-infrastructure attempt; original attempts are kept.

## Infrastructure repeats (retry lot 1)

| Task | Lot B failure | Retry result |
|---|---|---|
| batched-eval-parity | verifier refused: the stock Docker provider cannot enforce `allow_internet = false` on this kernel | verified 0 under `no_network_docker` (`network_mode: none`) |
| lake-temp-glm | same | verified 0 |
| layout-config-recreation2 | model provider closed the connection (`WebSocket closed 1012`) at request 103 | **passed** |
| wdm-design | same provider disconnect | **passed** |

No cell needed a second repeat; none was classified for manual review.

## Results per task

**Coverage:** 15/63 scored tasks passed; 63 of 63 planned tasks scored, 66 in the dataset. Excluded (lost coverage): fp8-rmsnorm-gemm, jax-speedrun-gpu, math-eval-grader. This is a **partial** run, not a full score.

**Attempts:** 67 across lots B, retry-1; estimated known USD 42.0070 (estimates, not invoices); 2 attempt(s) with unknown cost. Retry pending: none; exhausted: none; manual review: none.

| Task | Final lot | Attempts | Reward | Requests | Est. USD (final) |
|---|---|---|---:|---:|---:|
| atrx-vep-crispr | B | agent | 0 | 22 | 0.2602 |
| batched-eval-parity | retry-1 | infra:verifier, agent | 0 | 39 | 0.4074 |
| biped-contact-dynamics | B | agent | 1 | 31 | 0.5042 |
| bun-sourcemap-leak | B | agent | 0 | 8 | 0.0847 |
| cad-model | B | agent | 0 | 39 | 0.5123 |
| cargo-flight-dispatch | B | agent | 0 | 16 | 0.1759 |
| coq-block-bound | B | agent | 1 | 140 | 1.9760 |
| ctr-optimization | B | agent | 0 | 252 | 2.4654 |
| cumulative-layout-shift | B | agent | 1 | 62 | 0.8181 |
| data-anonymization | B | agent | 0 | 37 | 0.3337 |
| distributed-dedup | B | agent | 0 | 21 | 0.3123 |
| embedding-drift-monitor | B | agent | 0 | 17 | 0.1543 |
| fin-saccr-rwa | B | agent | 1 | 12 | 0.1795 |
| foodstuff-beta-activity | B | agent | 0 | 9 | 0.0983 |
| formal-crypto | B | agent | 0 | 72 | 1.1324 |
| freecad-impeller | B | agent | 0 | 17 | 0.1941 |
| freecad-platform-drawing | B | agent | 0 | 38 | 0.4045 |
| freecad-spring-clip | B | agent | 0 | 19 | 0.3792 |
| freight-dispatch-shift | B | agent | 0 | 30 | 0.6836 |
| glycan-ms2-elucidation | B | agent | 0 | 9 | 0.1386 |
| gsea-proteomics | B | agent | 0 | 25 | 0.2244 |
| heat-pump-warranty | B | agent | 0 | 49 | 0.4362 |
| hof-topology-interpenetration | B | agent | 0 | 34 | 0.6022 |
| html-js-filter | B | agent | 0 | 18 | 0.2445 |
| interleaved-vigenere | B | agent | 1 | 28 | 0.3015 |
| intrastat-meldung | B | agent | 0 | 51 | 0.5483 |
| ks-solver-cpp | B | agent | 0 | 17 | 0.2819 |
| kv-live-surgery | B | agent | 0 | 46 | 0.6512 |
| lake-temp-glm | retry-1 | infra:verifier, agent | 0 | 18 | 0.2043 |
| layout-config-recreation | B | agent | 0 | 105 | 1.9863 |
| layout-config-recreation2 | retry-1 | infra:provider, agent | 1 | 64 | 1.0175 |
| legacy-utility-triage | B | agent | 0 | 40 | 0.3858 |
| live-database-cutover | B | agent | 0 | 65 | 0.8738 |
| medical-claims-processing | B | agent | 0 | 41 | 0.4676 |
| mp-checkpoint-consolidation | B | agent | 1 | 54 | 0.6853 |
| music-harmony | B | agent | 0 | 21 | 0.2438 |
| mvcc-lsm-compaction | B | agent | 1 | 13 | 0.1155 |
| nextjs-performance | B | agent | 0 | 31 | 0.2752 |
| ontology-kg-querying | B | agent | 0 | 33 | 0.3705 |
| payments-pipeline-fix | B | agent | 0 | 41 | 0.4920 |
| photonic-waveguide-routing | B | agent | 0 | 14 | 0.3486 |
| pretrain-shard-corruption | B | agent | 1 | 128 | 4.3064 |
| production-planning | B | agent | 0 | 19 | 0.4533 |
| protein-autointerp-disulfide | B | agent | 0 | 6 | 0.1298 |
| react-lead-form | B | agent | 0 | 20 | 0.2717 |
| retro-console-soc | B | agent | 0 | 41 | 0.8184 |
| risk-scorer-replay | B | agent | 1 | 58 | 0.8190 |
| roy-polymorph-cn | B | agent | 0 | 9 | 0.0930 |
| rs-archive-clone | B | agent | 0 | 151 | 2.8401 |
| satb-audio-transcription | B | agent | 0 | 27 | 0.3736 |
| session-window-debug | B | agent | 0 | 17 | 0.1915 |
| sglang-qwen-burst | B | agent | 0 | 66 | 0.8571 |
| shadow-relay | B | agent | 1 | 35 | 0.6222 |
| sound-change-cascade | B | agent | 0 | 27 | 0.6130 |
| takens-embedding-lean | B | agent | 0 | 21 | 0.1837 |
| telecom-entity-resolution | B | agent | 0 | 54 | 0.7270 |
| uefi-bootkit | B | agent | 1 | 131 | 2.8297 |
| vba-userform-port | B | agent | 0 | 47 | 0.7481 |
| vf2-speedup-networkx | B | agent | 1 | 35 | 0.5415 |
| vllm-deepseek-streaming | B | agent | 0 | 42 | 0.4655 |
| vpp-loss-divergence | B | agent | 1 | 57 | 0.6338 |
| wal-recovery-ordering | B | agent | 0 | 20 | 0.2429 |
| wdm-design | retry-1 | infra:provider, agent | 1 | 41 | 0.3150 |


**Passed:** biped-contact-dynamics, coq-block-bound, cumulative-layout-shift, fin-saccr-rwa, interleaved-vigenere, layout-config-recreation2, mp-checkpoint-consolidation, mvcc-lsm-compaction, pretrain-shard-corruption, risk-scorer-replay, shadow-relay, uefi-bootkit, vf2-speedup-networkx, vpp-loss-divergence, wdm-design.

## Costs and receipts

67 attempts (63 lot B + 4 retries). Known estimated model usage **$42.0070**; 2 attempts have unknown cost because the provider dropped the connection with a request in flight (lot B `layout-config-recreation2`, `wdm-design`). No Jev calls. Receipts stay outside Git on the operator host, bound by SHA-256:

| File | SHA-256 |
|---|---|
| lot-b.json | `d87e21ee067b481044609373ed79cdf8ae408a40f70c1fdfff5bd2319dfced75` |
| authority-b.txt | `9adae2af96c856803468261c4a1adeec792467d03d35b46119fddd612a447b24` |
| ledger-b.jsonl | `7c2acdd0d952f610aa43f17e493ca2dd722d0db9d3f73f001ba2470734f812dd` |
| lot-b-retry1.json | `236fe9235dfec022d6b33364c76d2720530054cfe3e7961556eace261cba0536` |
| authority-b-retry1.txt | `facb2524d47cdd7167bbab5f0c789ac26091c7e17369016c972c0a1778a00307` |
| ledger-b-retry1.jsonl | `428b992840bced122dc975e8e82e04cf83bcf9508aef963a1bc9b1ee71e85fe5` |
| standard-full-summary.json | `88ba514284d43ffa8b320d3019d4538df2b0e077cd383412a86521876dbd69e7` |

Code: lot B ran at `dcafeb9ba5a64f7ed384ae8ad384466859d494d9`, retry lot 1 at `798a217f531027f14feb9ba01dc704288878d587`, both with green exact-head CI. The table above is produced by `standard_full_report.py` from the two Harbor job directories.

## Lot A (separate, not scored)

The first launch (lot A, code `62ea9f54`, capped at 48 requests/$57 per start, ledger SHA-256 `866dbc7bbc8add764a564b24a1e2177f55ee39d2dbfee0ab35d985df8d106cf3`) was stopped after two starts once the user lifted the budget: `layout-config-recreation2` exhausted its 48 requests and Harbor skipped the verifier (fixed by PR #349), and `photonic-waveguide-routing` was stopped after settlement. Two starts, about $1.72 estimated, no score; not mixed into the result above.

## Limits

- One repetition per task; no confidence interval. Harbor's official example uses `-k 5`.
- GPU tasks excluded; six CPU tasks request 16 GiB on a 15.3 GiB VM. The classifier detected no infrastructure failure for them, but an out-of-memory kill inside a task or verifier would look like an ordinary failure.
- The two no-network verifiers ran under our `network_mode: none` provider instead of Harbor's nftables sidecar; the enforced policy is the same (loopback only).
- Pi exposes only `sandbox_exec`; task-native MCP servers and skills (`medical-claims-processing`, `cumulative-layout-shift`) are not registered as Pi tools.
- Standard pilot (TBF-03, canceled) and the modified four-arm comparison (TBF-05) are separate experiments and are not combined with this result.
