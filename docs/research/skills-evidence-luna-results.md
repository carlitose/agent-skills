# Skills evidence candidate — Luna L4 results

## Artifact Graph
- Artifact ID: `artifact:skills-evidence-luna-results`
- Role: `research`
- Parent: [LEC-01](../tickets/skills-evidence-candidate/01-create-and-test.md)

## Verdict
Created and tested the first incremental candidate, `skills-evidence-v1`. Do not promote it over skills-only: one accepted delivery is an observed improvement over the current arm's zero, but no quality/cost/speed superiority is demonstrated. The complete proposed skills-only motor replacement is not implemented by this revision: it retains the historical stage choreography and native `--no-skills`; implementation guidance is explicit, not proof of automatic skill loading.

## Frozen treatment and method
Runtime CandidateRef v2: base tree `c7b2d7d7ee97750677c07f8cf08bb205b9097fd0`, candidate tree `5ca65dff23b68c25c98ab1e5c0eda67a2c95a5ee`, ticket digest `6deb0ed6aa74da12c3c2f8767d15e1bba9e003ffe756069a3188c5832389b3d6`. Source snapshot: `C:/dbench/tmp/lec01-local-tree-2`. One new serial cell for each original scenario, Luna medium, length four. None reused or replayed. Same corpus, SDK, policy/questions, images, process-owned tests, transport and oracle as the historical current arm. The old controller and adapter remain byte-identical; the new adapter selects the additive controller.

Changes are compact green receipt previews, verified full public ticket artifacts instead of repeated review/fix bodies, explicit inline implementation/behavior-test guidance, and actual bound coverage feedback to fix. Required test execution, global review, semantic YES, review veto, uncertainty gates and retry counts remain. No test-result caching or skipped review.

## Observed results
| Scenario | Private accepted / 4 | Attempted | Dependency-blocked | Cell seconds incl. oracle |
|---|---:|---:|---:|---:|
| Lua VM | 0/4 | 1 | 3 | 269.984 |
| SQL engine | 0/4 | 1 | 3 | 950.703 |
| Yjs | 1/4 | 3 | 1 | 1354.422 |
| Total | **1/12** | **5** | **7** | **2575.109 summed** |

Five product requests were attempted: one privately accepted and four privately rejected. Seven were never attempted. This is not eleven model failures. Lua/SQL R1 and Yjs R3 exhausted the three quality attempts; Yjs R4 was blocked. Yjs R1 passed both controller and private oracle. **Yjs R2 was controller-approved but rejected by the private oracle**: public green/review/semantic approval remains insufficient for benchmark acceptance. The unchanged advancement rule follows the controller, not hidden scoring, so Yjs R3 was legitimately attempted without leaking the R2 oracle result back to the participant.

All three native processes closed with exit0; launch/session/receipt identities are retained. No financial or infrastructure gate occurred. The sum42.919 minutes includes public work, private oracle and blocked-delivery snapshot scoring; it is not a measured whole-session wall-clock duration.

## Accounting and comparison limits
New cohort: **10,434,149 native tokens**, approximately **$0.192123** attributed experimental SDK estimate including eligible semantic work. Per-cell native SDK/token observations: Lua364,593/$0.009139; SQL875,862/$0.017564; Yjs9,193,694/$0.164723. The historical current cohort was0/12, three attempted/nine blocked,1,869,541 native tokens and about$0.04181 experimental estimate. More work advanced on Yjs, so full-cohort totals are not like-for-like efficiency rates. Lua/SQL still show no accepted output and no consistent token/cost reduction; no saving without quality loss is established.

Historical Luna skills-only9/36 remains indicative, not a controlled paired baseline; advancement and versions differ. Do not generalize the previous Opus scenario-specific frontier to this Luna candidate.

The original cumulative account was preserved in a new child store, without resetting the EUR1000 ceiling or changing historical authority/ledger. After this cohort:17 launches,119 reservations,35 semantic calls,684 charge identities; experimental cumulative estimate$0.425813. Operator checkpoint `C:/dbench/tmp/lec01-final-operator.json` records$34.988669 cumulatively since the original Luna mandate; combined$35.414482, aboutEUR31.345 using original reference FX. These are not the cost of this cohort alone or a provider invoice. Operator work after that checkpoint is unknown, not zero. Invoice and final FX remain unavailable.

## Local quality and remaining frontier
24 causal local tests passed in118.328s with real Git/public test processes and substituted AI ports. The first local attempt timed out at180s and remains retained, not converted to PASS. Local cumulative invocation time is at least298.328s; graph-inspection durations are unknown. Inline review/QA is shared-context, not independent. No full release profile or exact-head CI ran.

Next technical frontier: product-behavior coverage and false semantic approval, not additional orchestration. The current result does not authorize another cohort automatically. Release/source-stack integration, Git/provider delivery, installation and reload remain unperformed and separately gated.

## Primary evidence
- New manifests and cells: `C:/Users/CGS03/dbench-private/results/skills-evidence-luna-l4/cells/`.
- Retained cumulative child ledger: `C:/Users/CGS03/dbench-private/results/skills-evidence-luna-l4/budget.json`; historical parent remains unchanged.
- Reconciled hashes/counts: `C:/dbench/tmp/lec01-benchmark-facts.json`.
- Local attempts and snapshots: `C:/dbench/tmp/lec01-local-1.json`, `lec01-local-2.json`.
- Local review/QA: `C:/dbench/tmp/lec01-quality.md`.

No historical result, oracle, runtime snapshot or native count was overwritten; no commit, push, PR, merge, installation, reload or delegated worker was performed.
