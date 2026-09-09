# Local operational report

Use `scripts/report-local.py` when inspecting recorded phase costs or comparing controlled
local samples. It reads a canonical ledger through `AtomicLedger.load` and the existing
`Kernel.report` projection. It does not run the scheduler, append events, consume leaf
interactions, contact providers, create release gates, or write reports automatically.
Ordinary ledger locking may use the existing local lock file; ledger bytes stay unchanged.

```bash
python -B ticket-autopilot/scripts/report-local.py /absolute/run/ledger.json
python -B ticket-autopilot/scripts/report-local.py /absolute/run/ledger.json \
  --checks /absolute/local-checks.json --context /absolute/context.json
```

Output is JSON on stdout. Redirect it only to a separate local artifact, never over an input.
Invalid/unavailable input returns exit 2 and a content-free error. Inputs and retained log
paths are not followed recursively. Report source paths identify the explicitly selected
ledger/context/check report; no prompts, transcripts, argv, diagnostics, credentials or log
contents are exported. There is no daemon, database or external telemetry.

## Sources and units

| Field | Existing source | Meaning |
| --- | --- | --- |
| Phase duration | `history` leaf-result-recorded `details.wall_time` | Sum of reported values for leaf invocations at that pipeline stage, across candidate generations. The ledger does not persist units. Without a declaration, the unit is `unspecified`, not seconds. |
| Leaf observations | Matching immutable history events | Includes partial continuations; not retries. |
| Retry requests | quality-failed/final-tree-quality-stage-failed, `details.failures` below configured maximum | Nonterminal failure requests, not proof a rerun executed. Terminal failures do not add requests. Missing threshold/count observations remain unavailable. |
| Quality failures | Existing status ticket counter | Current counter, potentially reset; not necessarily lifetime requests. |
| Slowest observed | Recorded phase sums, descending; ticket/stage ties | Available only with a declared time unit. Ranks observed sums, including explicitly partial sums, not unknown whole-phase costs. |
| Check counts | Optional existing test-local schema-1 `records.status` | Check invocations, not test/subtest counts. That format records no durations: command time stays unavailable. |

`null` plus `availability: unavailable` is not zero. A recorded zero stays zero, with the
caveat that the leaf caller may have supplied its default rather than a measured duration.
A partial sum reports its valid observation and missing-value counts; comparisons never
subtract partial sums as complete totals. Unit-free raw values remain visible, but temporal
ranking and comparisons remain unavailable until units are declared from known provenance.
This does not add units to the historical ledger or prove the declaration. No duration is
inferred from a timeout allowance, file timestamp or absence of activity. Session time and model tokens remain unavailable.
The [token-economics investigation](../../docs/specs/autopilot-token-economics-wayfinder.md)
owns live-token work; static bytes are not model tokens.

## Controlled comparison

Supply a context JSON for each sample with exactly four nonempty string fields:

```json
{"workload":"fixture-v1; same tickets and input sizes","environment":"OS/Python/Git/hardware versions","protocol":"serial; explicit timing; same command profile and provider mode","wall_time_unit":"seconds"}
```

These are operator-declared comparison conditions, not discovered historical environment
facts. `wall_time_unit` accepts `seconds`, `milliseconds`, or `unspecified`; it labels the
recorded values and never rescales or guesses them. Use `unspecified` when provenance is
unknown. Do not declare one unit for a history that mixes units. Record input/workload
versions, OS, Python, Git, hardware, concurrency, provider mode and measurement procedure
accurately. Optional check artifacts retain only their profile
and recorded version/platform metadata, separately from ledger timing; they are not
automatically proven to belong to that ledger run.

```bash
python -B ticket-autopilot/scripts/report-local.py /absolute/left/ledger.json \
  --context /absolute/left-context.json --checks /absolute/left-checks.json \
  --compare-ledger /absolute/right/ledger.json \
  --compare-context /absolute/right-context.json --compare-checks /absolute/right-checks.json
```

Missing context or unspecified units returns `unavailable`; differing declared context,
recorded check environment or ticket IDs returns `incomparable` with no deltas. Matching inputs are only
`declared-comparable`: deltas are **right minus left**, not speedup or causation claims.
Do not use equal labels to conceal different workloads or environments.

Deterministic provider-free examples live in `tests/test_local_report.py`: a recorded review
zero versus an unobserved QA phase; 1.5 recorded units plus missing values yielding a
partial sum; continuation events versus nonterminal/terminal failures; and two synthetic
review observations, 2 and 5 seconds, yielding +3 under the same declared context. These
are fabricated unit inputs, not measured performance runs. Real-ledger CLI tests assert
byte equality and reject any save, event append, subprocess or provider call.

A comparison is usable only when every input is identified, units and missing observations
remain visible, and declared conditions are genuinely equivalent. A report does not change
quality or release policy.
